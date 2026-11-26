# ENV: environments and deprecated APIs

## ENV-01 Sandbox host or default environment in a production build

Severity: High.

**Search:**

```bash
rg -n -e 'sandbox\.cleeng\.com' -e 'mediastoreapi-sandbox' -e 'srm-sandbox' <scope>
rg -n -e 'setEnvironment' -e '@cleeng/mediastore-sdk' <client>
```

Read build configuration: `.env.production`, `next.config.*`, `vite.config.*`, Gradle `buildTypes` and `productFlavors`, Xcode `.xcconfig` files and schemes, CI deploy variables.

**Judge.**

- Confirmed: a sandbox host is the value for a production build, or the only value with no per-environment switch.
- Confirmed: the app uses `@cleeng/mediastore-sdk` and never calls `Config.setEnvironment('production')`. The SDK defaults to sandbox.
- Likely: one variable holds the base URL and production configuration does not set it.
- Not a finding: sandbox hosts in test, staging or development configuration.

**Why.** Production viewers would sign in and pay against the sandbox, which has separate accounts and keys.

**Fix.** Select hosts and keys per build. Call `Config.setEnvironment('production')` in production builds of the MediaStore SDK.

**Source.** [Enterprise Go Live Checklist](https://publisher.support.cleeng.com/hc/en-us/articles/4417301124252), item 2: "Ensure that you are using production endpoints* with your production ID". [mediastore-sdk README](https://github.com/Cleeng/mediastore-sdk): `setEnvironment` defaults to `sandbox`.

## ENV-02 JSON-RPC API 3.0 in use

Severity: High.

**Search:**

```bash
rg -n -e '3\.0/json-rpc' -e 'json-rpc' -e '"jsonrpc"\s*:\s*"2\.0"' <scope>
rg -n -e 'getAccessStatus' -e 'listCustomerSubscriptions' -e 'generateCustomerToken' -e 'getCustomer\b' -e 'registerCustomer' -e 'getOfferDetails' -e 'updateCustomerSubscription' -e 'getAccessibleTags' -e 'isTrialAllowed' -e 'extendTokenExpiration' -e 'customerToken' <scope>
```

**Judge.** Confirmed when code calls the JSON-RPC endpoint, or sends a JSON-RPC body with a Cleeng method name. A `customerToken` read from a MediaStore login response and passed to JSON-RPC counts.

**Why.** Cleeng decommissions JSON-RPC on 1 April 2027. After that, every call fails.

**Fix.** Read `json-rpc-migration.md` and give the replacement for each method found. List the methods without a direct replacement and tell the user to ask Cleeng about them.

**Source.** [Upcoming Legacy JSON-RPC API Service Decommission](https://publisher.support.cleeng.com/hc/en-us/articles/27764552952988): "On April 1, 2027, the JSON-RPC service will be fully decommissioned".

## ENV-03 Other deprecated endpoints and fields

Severity: Low.

**Search:**

```bash
rg -n -e 'cleengSection' -e 'USER0004' -e 'totalPrice' -e 'methodFee' -e 'revive' <scope>
rg -n -e 'subscriptions/' <files with Core API calls>
```

**Judge.**

- Confirmed: `PATCH /3.1/subscriptions/{id}` with a `status` field. Use the action endpoints (`/cancel`, `/terminate`, `/pause`, `/resume`).
- Confirmed: `totalPrice` or `methodFee` sent on create order. Cleeng calculates the price; send neither.
- Confirmed: logic that depends on `404 USER0004` from `PUT /customers/passwords`. Since 23 November 2026 the endpoint returns 200 for unknown emails; do not use it to test whether an account exists.
- Confirmed: the `cleengSection` query parameter for hosted widgets. Use `data-cleeng-widget` values.

**Why.** Each item is deprecated or has changed behaviour; code that depends on it breaks or silently does nothing.

**Fix.** The replacement for each item is in its Judge bullet.

**Source.** [Release Notes 2026.04.09](https://publisher.support.cleeng.com/hc/en-us/articles/26673178605852) and later release notes in the publisher Help Center.
