# AUTH: credentials and identity

## AUTH-01 Publisher token or Core API call in client code

Severity: Critical.

**Search** in `<client>` folders only:

```bash
rg -n -i -e 'x-publisher-token' -e 'publisherToken' <client>
rg -n -e 'api(\.sandbox)?\.cleeng\.com' -e '/3\.1/' -e '3\.0/json-rpc' -e 'generateCustomerToken' <client>
rg -n -e 'webhook\.api\.(prod|sandbox)\.cleeng\.com' -e '/sso/auths' <client>
```

Also look for build-time variables that inject a token into a client bundle: `VITE_*`, `NEXT_PUBLIC_*`, `REACT_APP_*`, `EXPO_PUBLIC_*`, `BuildConfig` fields, `Info.plist` keys whose name mentions publisher token or API key.

**Judge.**

- Confirmed: client code sends `X-Publisher-Token` or a `publisherToken` param, or calls Core API 3.1, JSON-RPC, the Webhook Management API or `/sso/auths`.
- Confirmed: a client build variable holds a publisher token, even if no call site is visible.
- Not a finding: the same code in a server folder, or a server-side rendering path that never ships to the browser. Check that the file is not imported by client bundles (for example a Next.js file without `"use client"` and only used from API routes).

**Why.** The publisher token authorises every Core API call for the publisher, including reading any customer and creating access. Anyone can extract it from a browser bundle or an app binary.

**Fix.**

1. Move the call to the integrator's backend, and let the client call that backend.
2. Client apps that need Cleeng data directly use MediaStore API with the customer's JWT.
3. Treat the token as leaked: generate a new API key in the Cleeng dashboard, restrict it by IP, and delete the old one.

```ts
// Before (browser)
fetch("https://api.cleeng.com/3.1/entitlements?customerId=" + id, {
  headers: { "X-Publisher-Token": import.meta.env.VITE_CLEENG_TOKEN },
});

// After (browser): MediaStore API with the customer's JWT
fetch(`https://mediastoreapi.cleeng.com/entitlements/${offerId}`, {
  headers: { Authorization: `Bearer ${jwt}` },
});
```

**Source.** [Getting Started With Core API](https://developers.cleeng.com/reference/api31): "Core API (API 3.1) is designed for Server-to-Server integrations. It uses a publisher token". [Android](https://developers.cleeng.com/docs/android): "middleware is required in integrations utilizing a publisher token". [API Key](https://publisher.support.cleeng.com/hc/en-us/articles/218389137): IP restriction per key.

## AUTH-02 Credential literal in source or committed config

Severity: High.

**Search** in all folders:

```bash
rg -n -i -e '(publisher_?token|x-publisher-token|cleeng_?(api_?)?key|api_?key)\W{1,8}[A-Za-z0-9_-]{40,}' <scope>
rg -n -e 'whsec_[A-Za-z0-9+/=]{20,}' <scope>
rg -n -i -e 'cleeng' -g '.env*' -g '!*.example' -g '!*.sample' <scope>
```

**Judge.**

- Confirmed: a literal of 40 or more token characters assigned to a name that means publisher token, API key or webhook secret, in a tracked file.
- Confirmed: a committed `.env` file with a Cleeng token value. Check `.gitignore` and `git ls-files` when available.
- Not a finding: placeholders (`<your-token>`, `xxxx`, `changeme`), `.env.example` files with empty values, test fixtures that use obviously fake values.

Never print the value. Quote the line with the value replaced by `<redacted>`.

**Why.** A literal lands in git history, CI logs and every clone of the repository. Removing it from the latest commit does not remove it from history.

**Fix.** Read the value from a secret store or an environment variable set at deploy time. Generate a new key in the Cleeng dashboard and delete the old one; rewriting git history is not enough.

**Source.** [Quick Start](https://developers.cleeng.com/docs/quick-start): "the API key will be displayed only once. Copy it immediately and store it securely". [Webhooks Configuration](https://developers.cleeng.com/docs/webhooks-configuration): "The signing secret is strictly confidential".

## AUTH-03 Cleeng JWT trusted without a signature check

Severity: High.

**Search** in `<server>` folders:

```bash
rg -n -e 'jwt\.decode\(' -e 'jwtDecode\(' -e 'jwt_decode\(' -e 'decode_jwt' -e 'JWT::decode' -e 'atob\(' -e "split\(['\"]\\.['\"]\)" <server>
rg -n -e 'customerId' <server>
```

**Judge.**

- Confirmed: server code reads `customerId` (or any claim) from a token it received from a client, and never verifies the signature. Signs: `jwt.decode` without `verify`, `jwt.decode(token, options={"verify_signature": False})`, base64-decoding the middle segment.
- Not a finding: decoding in client code to read `exp`. The client only needs to know when to refresh.
- Not a finding: the server verifies with a JWKS client or the Cleeng public key before reading claims.

**Why.** A token with another customer's id passes an unverified check, and the backend acts for the wrong customer.

**Fix.** Verify RS256 against Cleeng's JWKS and cache the key set.

```js
import { createRemoteJWKSet, jwtVerify } from "jose";
const jwks = createRemoteJWKSet(new URL("https://identity.api.prod.cleeng.com/.well-known/jwks.json"));
const { payload } = await jwtVerify(token, jwks, { algorithms: ["RS256"] });
const customerId = payload.customerId;
```

**Source.** [Getting Started with Authentication API](https://developers.cleeng.com/reference/getting-started-with-authentication-api): "you must validate it … The recommended method is to use the JWKS".

## AUTH-04 Publisher token and customer JWT on the same Core API request

Severity: High.

**Search** in `<server>` folders:

```bash
rg -n -i -e 'x-publisher-token' <server>
rg -n -i -e 'authorization' -e 'bearer' <server>
```

**Judge.** Confirmed when one HTTP client or request to `/3.1/` sets both `X-Publisher-Token` and `Authorization: Bearer`. Shared client defaults count: a base client with a default `Authorization` header plus a per-call publisher token.

**Why.** Core API rejects the whole request when one of several credentials is invalid. A stale customer JWT then breaks a call the publisher token alone would authorise.

**Fix.** Send only `X-Publisher-Token` to Core API 3.1. Keep a separate HTTP client for MediaStore calls that carry a JWT.

**Source.** Cleeng recommendation.

## AUTH-05 Viewer IP missing on server-side calls

Severity: High.

**Search** in `<server>` folders:

```bash
rg -n -e '/sso/auths' -e '/auths\b' -e "/customers['\"\`]" -e '/orders' -e '/offers' -e '/purchases' -e 'registerCustomer' -e 'generateCustomerToken' <server>
rg -n -e 'customerIP' -e 'customerIp' -e 'ipAddress' <server>
```

**Judge.**

- Confirmed: a server-side call to `POST /sso/auths`, `POST /auths`, `POST /customers` (register), `POST /orders`, offer endpoints or In-App `POST …/purchases` sends no `customerIP` (`ipAddress` for In-App).
- Confirmed: the field is set to the server's own address or a constant.
- Likely: the field is set from `req.ip` or `REMOTE_ADDR` behind a proxy or CDN without trusting `X-Forwarded-For`. Say which header the deployment should use.

**Why.** Cleeng uses the viewer's IP for geo-restriction, tax, price and fraud checks. Without it, every viewer looks like the backend, and Cleeng records the same address for many customers.

**Fix.** Forward the viewer's IP from the incoming request on every such call.

```js
// Express behind one proxy: app.set("trust proxy", 1) makes req.ip the client address
await mediastore.post("/sso/auths", { email, customerIP: req.ip }, { headers: { "X-Publisher-Token": token } });
```

**Source.** [SSO Login](https://developers.cleeng.com/reference/sso-login): "While it is not mandatory due to backward compatibility, it should be provided at all times." [Register](https://developers.cleeng.com/reference/register): "It is recommended that customerIP is passed in the register, login and create order methods." [Offer display](https://developers.cleeng.com/docs/offer-display): "Always pass customerIP if you are making the request from the backend". [Enterprise Go Live Checklist](https://publisher.support.cleeng.com/hc/en-us/articles/4417301124252), item 26.

## AUTH-06 Tokens or customer data written to logs

Severity: Medium.

**Search** near Cleeng call sites in all folders:

```bash
rg -n -e 'console\.(log|info|debug)' -e 'logger\.' -e 'log\.(info|debug)' -e 'Log\.d' -e 'print\(' -e 'NSLog' -e 'error_log' <files with Cleeng call sites>
```

**Judge.** Confirmed when a log call prints a JWT, a refresh token, `X-Publisher-Token`, a whole request or response object of a Cleeng call, or customer emails. Logging a status code, an error code or a request id is fine.

**Why.** Logs are kept for months and read by many people and tools. A refresh token in a log stays usable for up to 100 days.

**Fix.** Log the method, path, status, Cleeng error code and request id. Redact `jwt`, `refreshToken`, `X-Publisher-Token` and email fields, or use the logger's redaction option.

**Source.** Cleeng recommendation.
