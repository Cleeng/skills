# Cleeng API surface

The Cleeng hosts, endpoints, headers and SDK names to search for, and which credential each API takes.

Checked against developers.cleeng.com on 2026-11-26.

## Search conventions

The searches in this skill are written for ripgrep. With grep, use `grep -rnE`; with the agent's own search tool, use the same regular expressions.

ripgrep skips files listed in `.gitignore`. Also exclude vendored and generated code:

```bash
RG_EXCLUDES=(-g '!node_modules' -g '!vendor' -g '!Pods' -g '!dist' -g '!build' -g '!.next' -g '!*.min.js' -g '!*.map' -g '!*.lock' -g '!package-lock.json')
rg -n "${RG_EXCLUDES[@]}" -e '<pattern>' <paths>
```

Where a Search block says `<client>` or `<server>`, pass the folders from step 1.

## Inventory searches

Run these over the whole scope:

```bash
# Hosts
rg -n -i -e 'cleeng\.com' -e 'cleeng\.js' <scope>

# SDK and widgets
rg -n -e '@cleeng/mediastore-sdk' -e 'data-cleeng-widget' -e 'window\.cleeng' -e 'cleengSection' <scope>

# Credentials and Cleeng-specific headers
rg -n -i -e 'x-publisher-token' -e 'publisherToken' -e 'x-publisher-id' -e 'x-webhook-signature' -e 'x-webhook-delivery-id' <scope>

# Endpoints that are distinctive enough to search on their own
rg -n -e '/auths/refresh_token' -e '/sso/auths' -e '/entitlements' -e 'json-rpc' -e '/purchases/synchronizations' -e 'webhook_subscriptions' <scope>

# Base URLs kept in configuration
rg -n -i -e 'cleeng' -g '*.env*' -g '*.json' -g '*.yml' -g '*.yaml' -g '*.toml' -g '*.plist' -g '*.xml' -g '*.properties' -g '*.gradle*' -g '*.xcconfig' <scope>
```

Base URLs often sit in configuration and paths in code. When a client builds URLs as `${BASE}/customers/${id}`, follow `BASE` to its value.

## Hosts

| API | Production | Sandbox |
|---|---|---|
| MediaStore API | `mediastoreapi.cleeng.com` | `mediastoreapi-sandbox.cleeng.com` |
| Core API 3.1 and legacy JSON-RPC 3.0 | `api.cleeng.com` | `api.sandbox.cleeng.com` |
| In-App API | `inapp.api.prod.cleeng.com` | `inapp.api.sandbox.cleeng.com` |
| Webhook Management API | `webhook.api.prod.cleeng.com` | `webhook.api.sandbox.cleeng.com` |
| Authentication API (device login, JWKS) | `auth.api.prod.cleeng.com` | `auth.api.sandbox.cleeng.com` |
| Identity (JWKS) | `identity.api.prod.cleeng.com` | `identity.api.sandbox.cleeng.com` |
| Hosted widgets script | `widgets.prod.cleeng.com/cleeng.js` | `widgets.sandbox.cleeng.com/cleeng.js` |

Legacy in-app notification host: `notification.cleeng.com/2.0/in_app/…` (deprecated).

## Credentials

| API | Credential | Where it may live |
|---|---|---|
| MediaStore API | Customer JWT, `Authorization: Bearer <jwt>` | Client apps |
| MediaStore `POST /sso/auths` | Publisher token, `X-Publisher-Token` | Server only |
| Core API 3.1 | Publisher token, `X-Publisher-Token` | Server only |
| JSON-RPC 3.0 | `publisherToken` or `customerToken` in the request params | Server only for `publisherToken`; the whole API is being decommissioned |
| In-App API | Customer JWT (direct integrations) or publisher token (through a backend), plus `X-Publisher-Id` | JWT in clients; publisher token on servers only |
| Webhook Management API | Publisher token | Server only |
| Webhook delivery to the integrator | `X-Webhook-Signature`, HMAC-SHA256 with the endpoint's signing secret | The secret stays on the server |

A publisher token and a customer token both look like 48 characters from `[A-Za-z0-9_-]`. Judge a literal by the name it is assigned to and where it is sent, not by its shape alone.

## Token facts

- Customer JWT: RS256, expires after 15 minutes. Claims include `customerId`, `publisherId` and `exp`. Verify with JWKS at `https://identity.api.prod.cleeng.com/.well-known/jwks.json`.
- Refresh token: valid for 100 days, single use. `POST /auths/refresh_token` returns a new JWT and a new refresh token and invalidates the one sent.
- Refresh errors: `401 AUTH0003` means the refresh token is expired or unknown. `409 MSSDK0101` means another refresh with the same token is in progress.
- A sign-in (`POST /auths` or `POST /sso/auths`) costs Cleeng a customer lookup, a database write and a new refresh token. A refresh is one token swap.
- MediaStore rate limit per customer per endpoint: up to 20 requests in quick succession, within 100 requests per 15 minutes. Over the limit: `429` with code `MSSDK0002`.

## MediaStore API endpoints (customer JWT unless noted)

| Purpose | Endpoint |
|---|---|
| Sign in with password | `POST /auths` (no JWT) |
| SSO sign-in from a backend | `POST /sso/auths` (publisher token, server only) |
| Refresh | `POST /auths/refresh_token` (no JWT) |
| Sign out everywhere | `DELETE /refresh_tokens` |
| Register | `POST /customers` (no JWT) |
| Customer | `GET`/`PATCH /customers/{customerId}` |
| Subscriptions, passes, offers, transactions | `GET /customers/{customerId}/subscriptions`, `/passes`, `/offers`, `/transactions` |
| Payment details | `GET /customers/{customerId}/payment_details` |
| Entitlement for one offer | `GET /entitlements/{offerId}` |
| Offers | `GET /offers`, `GET /offers/{offerId}`, `GET /v2/offers/{offerId}` |
| Orders and payments | `POST /orders`, `/connectors/adyen/…`, `/connectors/paypal/…` |
| Locale from IP | `GET /locales` |
| Password reset | `PUT /customers/passwords` |

## Core API 3.1 endpoints (publisher token, server only)

| Purpose | Endpoint |
|---|---|
| Find customer by email | `GET /3.1/customers?email=<url-encoded>&limit=1` |
| Customer by id | `GET`/`PATCH /3.1/customers/{customerId}` |
| Entitlements for a customer | `GET /3.1/entitlements?customerId=…` |
| Entitlement for one offer | `GET /3.1/entitlements/customer_id/{customerId}/offer_id/{offerId}` |
| Subscriptions | `GET /3.1/subscriptions`, `POST /3.1/subscriptions/{id}/cancel`, `/terminate`, `/pause`, `/resume` |
| Offers | `/3.1/offers…` |

## Webhooks

- Management: `POST /endpoints`, `PATCH /endpoints/{id}`, `DELETE /endpoints/{id}`, `POST /endpoints/{id}/rotate-secret` on the Webhook Management API.
- Delivery headers: `X-Webhook-Signature`, `X-Webhook-Delivery-Id` (stable across retries), `X-Webhook-Attempt`, `X-Webhook-Max-Attempts`. User agent `Cleeng Webhook Engine`.
- Body: `{"broadcasterId": …, "topic": "…", "data": {…}}`.
- Common topics: `subscriptionCreated`, `subscriptionRenewed`, `subscriptionTerminated`, `subscriptionSwitched`, `subscriptionPaused`, `subscriptionResumed`, `passCreated`, `passTerminated`, `customerUpdated`, `customerDeleted`, `paymentRefunded`, `inappPurchaseSyncResult`.

## In-App API

| Store | Endpoints |
|---|---|
| Apple StoreKit 2 | `POST /storekit2/purchases`, `GET /storekit2/purchases/synchronizations/{id}`, `POST /storekit2/purchases/transfers` |
| Google Play | `POST /google-play/purchases`, `GET /google-play/purchases/synchronizations/{id}`, `POST /google-play/purchases/transfers` |
| Samsung TV, Vizio | `POST /{samsung-tv,vizio}/purchase-validation`, `GET /{samsung-tv,vizio}/purchase-status` |
| Roku, Amazon | `POST /roku/purchases…`, `POST /amazon/payment` |
