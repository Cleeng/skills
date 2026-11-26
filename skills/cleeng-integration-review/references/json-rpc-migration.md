# JSON-RPC 3.0 migration

Used by ENV-02. Give the replacement for each method found. Cleeng decommissions JSON-RPC on 1 April 2027.

The JSON-RPC `customerToken` has no replacement. Client apps use the customer JWT from MediaStore API; servers use the publisher token with Core API 3.1.

| JSON-RPC method | Replacement |
|---|---|
| `getAccessStatus` | Client: MediaStore `GET /entitlements/{offerId}`. Server: `GET /3.1/entitlements/customer_id/{customerId}/offer_id/{offerId}`. Gate on `accessGranted`. |
| `getCustomer` | Client: MediaStore `GET /customers/{customerId}`. Server: `GET /3.1/customers/{customerId}`. |
| `generateCustomerToken` | Server, after the identity provider signs the user in: MediaStore `POST /sso/auths` with the publisher token and `customerIP`. |
| `generateCustomerTokenFromPassword` | MediaStore `POST /auths`. |
| `extendTokenExpiration` | MediaStore `POST /auths/refresh_token` (see SESS-01). |
| `registerCustomer` | Client: MediaStore `POST /customers`. Server: `POST /3.1/customers`. |
| `requestPasswordReset` | MediaStore `PUT /customers/passwords`. |
| `updateCustomerEmail` | Server: `PATCH /3.1/customers/{customerId}`. |
| `listCustomerSubscriptions` | Server: `GET /3.1/subscriptions` filtered by customer. Client: MediaStore `GET /customers/{customerId}/subscriptions`. Do not use it to grant access (ENT-01). |
| `updateCustomerSubscription` | Server: the subscription action endpoints, such as `POST /3.1/subscriptions/{id}/cancel`, `/pause`, `/resume`. |
| `listSubscriptionOffers`, `listPassOffers` | Server: `GET /3.1/offers`. Client: MediaStore `GET /offers`. |
| `getOfferDetails` | Client: MediaStore `GET /offers/{offerId}` or `GET /v2/offers/{offerId}`. Server: `GET /3.1/offers/{offerId}`. |
| `getLocaleDataFromIp` | MediaStore `GET /locales`. |
| `subscribeToWebhookEvent` | Webhook Management API `POST /endpoints` (see HOOK-05). |
| `getConsentDefinitions`, `getViewerConsents`, `submitConsent` | MediaStore `GET /publishers/{publisherId}/consents`, `GET`/`PUT /customers/{customerId}/consents`. |
| `isTrialAllowed`, `getAccessibleTags`, capture methods | No direct replacement listed in the public docs. Tell the user to ask Cleeng support for the supported alternative. |

Check each replacement against the current reference at https://developers.cleeng.com before changing code. The response shapes differ from JSON-RPC.
