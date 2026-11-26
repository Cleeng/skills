# Rule index

Every rule this skill checks, with the reference file that holds its searches, judgement and fix.

| Severity | Meaning |
|---|---|
| Critical | A credential is exposed, or the integration accepts forged events. Fix before the next release. |
| High | The code multiplies Cleeng calls per viewer, grants or denies access wrongly, or uses an API that is removed or has a removal date. |
| Medium | The code fails under load or in edge cases. |
| Low | Hygiene. |

| ID | Check | Severity | File |
|---|---|---|---|
| AUTH-01 | Publisher token or Core API call in client code | Critical | `auth.md` |
| AUTH-02 | Credential literal in source or committed config | High | `auth.md` |
| AUTH-03 | Cleeng JWT trusted without a signature check | High | `auth.md` |
| AUTH-04 | Publisher token and customer JWT on the same Core API request | High | `auth.md` |
| AUTH-05 | Viewer IP missing on server-side calls | High | `auth.md` |
| AUTH-06 | Tokens or customer data written to logs | Medium | `auth.md` |
| SESS-01 | Sign-in where a token refresh would do | High | `session.md` |
| SESS-02 | Rotated refresh token not stored | High | `session.md` |
| SESS-03 | Concurrent refresh calls | Medium | `session.md` |
| SESS-04 | Refresh on a timer or before every call | Medium | `session.md` |
| SESS-05 | Cleeng read used as a session check | Medium | `session.md` |
| SESS-06 | Refresh errors handled wrongly | Medium | `session.md` |
| SESS-07 | Tokens kept after sign-out | Low | `session.md` |
| LOAD-02 | Account data read on every screen | High | `call-volume.md` |
| LOAD-03 | Customer looked up by email on each request | High | `call-volume.md` |
| LOAD-04 | Email lookup built wrongly | Medium | `call-volume.md` |
| LOAD-05 | Cleeng polled on a timer | High | `call-volume.md` |
| LOAD-06 | Checkout mounted for viewers who already have access | Medium | `call-volume.md` |
| LOAD-07 | Static data fetched per request | Low | `call-volume.md` |
| LOAD-08 | Load tests or unthrottled bulk jobs against Cleeng | Medium | `call-volume.md` |
| ENT-01 | Access granted from the wrong field | High | `entitlements.md` |
| ENT-02 | Entitlement checked more than once per play | High | `entitlements.md` |
| ENT-03 | Per-offer entitlement calls in a loop | Medium | `entitlements.md` |
| ENT-04 | Entitlement cache that cannot go stale | Medium | `entitlements.md` |
| ENT-05 | Cached entitlements not re-checked within 24 hours | Low | `entitlements.md` |
| RES-01 | No timeout on Cleeng calls | Medium | `resilience.md` |
| RES-02 | Aggressive retries | High | `resilience.md` |
| RES-03 | 429 not handled | Medium | `resilience.md` |
| RES-04 | Writes retried without protection | Medium | `resilience.md` |
| RES-05 | One circuit breaker for every Cleeng call | Low | `resilience.md` |
| HOOK-01 | Webhook signature not verified | Critical | `webhooks.md` |
| HOOK-02 | Webhook signature computed wrongly | High | `webhooks.md` |
| HOOK-03 | Webhook handler not idempotent | Medium | `webhooks.md` |
| HOOK-04 | Transient webhook failures answered with 4xx, or slow handlers | High | `webhooks.md` |
| HOOK-05 | Removed webhook API or topic | High | `webhooks.md` |
| IAP-01 | Store transactions not all registered with Cleeng | High | `in-app-purchases.md` |
| IAP-02 | Purchase sync responses mishandled | Medium | `in-app-purchases.md` |
| IAP-03 | Unbounded purchase-sync polling | Medium | `in-app-purchases.md` |
| IAP-04 | Duplicate purchase not prevented | Medium | `in-app-purchases.md` |
| IAP-05 | Deprecated in-app endpoints | Medium | `in-app-purchases.md` |
| IAP-06 | Missing `X-Publisher-Id` on In-App API calls | Low | `in-app-purchases.md` |
| ENV-01 | Sandbox host or default environment in a production build | High | `environments.md` |
| ENV-02 | JSON-RPC API 3.0 in use | High | `environments.md` |
| ENV-03 | Other deprecated endpoints and fields | Low | `environments.md` |
| WEB-01 | `cleeng.js` self-hosted or loaded repeatedly | Medium | `web-widgets-sdk.md` |
| WEB-02 | Tokens rotated by widgets or SDK not persisted | High | `web-widgets-sdk.md` |
| WEB-03 | External SSO with profile or password editing in the Account widget | Medium | `web-widgets-sdk.md` |
| WEB-04 | No bot protection on register and purchase | Medium | `web-widgets-sdk.md` |
