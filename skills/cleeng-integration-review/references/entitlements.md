# ENT: entitlement checks

Entitlement endpoints: `GET /entitlements/{offerId}` on MediaStore API (customer JWT, client), and `GET /3.1/entitlements?customerId=…` or `GET /3.1/entitlements/customer_id/{customerId}/offer_id/{offerId}` on Core API (publisher token, server). Each response carries `accessGranted`.

## ENT-01 Access granted from the wrong field

Severity: High.

**Search:**

```bash
rg -n -e 'expiresAt' -e 'expiryDate' -e 'expires_at' -e 'getAccessStatus' <scope>
rg -n -e 'accessGranted' <scope>
rg -n -e '/subscriptions' -e '/customers/[^ ]*/offers' -e 'listCustomerSubscriptions' <scope>
```

**Judge.**

- Confirmed: playback or content access depends on `expiresAt` or another expiry date compared with the clock.
- Confirmed: access depends on a subscription's `status`, or on the presence of an item in `GET /customers/{id}/subscriptions`, `/customers/{id}/offers` or `listCustomerSubscriptions`.
- Confirmed: access depends on JSON-RPC `getAccessStatus` (also ENV-02).
- Not a finding: `expiresAt` shown as text ("renews on …") while access depends on `accessGranted`.

**Why.** `accessGranted` accounts for grace periods, pauses and terminations. Expiry dates and subscription lists do not, so viewers lose access they paid for or keep access after termination.

**Fix.** Gate playback on `accessGranted` from an entitlements endpoint: `GET /entitlements/{offerId}` in clients, `GET /3.1/entitlements…` on servers.

**Source.** [Unlocking content with entitlements](https://developers.cleeng.com/docs/unlocking-content-with-entitlements): "accessGranted: This is the only field you need to check for playback" and "expiresAt: Do not use this for granting access". [Fetch customer's subscriptions](https://developers.cleeng.com/reference/fetch-customers-subscriptions): "this API should not be used for validating entitlements - please use Get entitlements instead."

## ENT-02 Entitlement checked more than once per play

Severity: High.

**Search:**

```bash
rg -n -e '/entitlements' -e 'checkAccess' -e 'hasAccess' -e 'isEntitled' -e 'checkEntitlement' <scope>
```

Follow each entitlement call to its callers: list and grid renderers, tile or card components, browse screens, player heartbeats, segment or chunk hooks.

**Judge.**

- Confirmed: an entitlement call runs once per tile, card or row on a browse screen, with no cache.
- Confirmed: the player re-checks on each segment or chunk. A re-check on a timer is LOAD-05.
- Likely: every screen re-checks with no cache in between.
- Not a finding: one fresh check when playback starts, and cached answers on browse screens.

**Why.** Browse screens multiply checks by the number of tiles, and in-playback checks multiply them by viewing time. Each check is a full API call on Cleeng's side.

**Fix.** Check fresh when playback starts. Browse screens use a cached answer per customer and offer, kept for a few minutes. Do not re-check during playback. Drop the cache entry after a purchase and on subscription webhooks (ENT-04).

**Source.** [Unlocking content with entitlements](https://developers.cleeng.com/docs/unlocking-content-with-entitlements): check "immediately after user login … and again right before serving any specific asset". [API Caching](https://developers.cleeng.com/reference/api-caching).

## ENT-03 Per-offer entitlement calls in a loop

Severity: Medium.

**Search:**

```bash
rg -n -e 'entitlements/' <scope>
```

Read the surrounding code for `for`, `forEach`, `map`, `Promise.all`, `ForEach`, `compactMap` or `async let` over offers.

**Judge.** Confirmed when the code calls `GET /entitlements/{offerId}` for each offer in a list.

**Why.** The MediaStore rate limit is per customer per endpoint, and all offers go through the same entitlement endpoint. A loop over ten offers spends ten requests of the same allowance on one screen.

**Fix.** On a server, use one `GET /3.1/entitlements?customerId=…` call and read all offers from it. In a client, check only the offer the viewer is about to play, and use cached answers for the rest (ENT-02).

**Source.** [Getting Started](https://developers.cleeng.com/reference/getting-started): MediaStore rate limit per customer per endpoint.

## ENT-04 Entitlement cache that cannot go stale

Severity: Medium.

**Search:**

```bash
rg -n -i -e 'cache' -e 'ttl' -e 'maxAge' -e 'expire' <files with entitlement calls>
rg -n -e 'subscriptionTerminated' -e 'subscriptionCreated' -e 'passTerminated' <scope>
```

**Judge.**

- Confirmed: an entitlement cache has no TTL.
- Confirmed: the cache is not cleared after an in-app or web purchase made in the app.
- Likely: the cache is kept current by webhooks alone, with a TTL longer than a day.
- Not a finding: a TTL of minutes, cleared on purchase and on subscription webhooks.

**Why.** A webhook can fail to arrive: Cleeng does not retry a delivery answered with 4xx. A cache without a TTL then keeps access open after a termination, or keeps it closed after a purchase.

**Fix.** Give the cache a TTL. Clear the entry after a purchase. Update or clear it on `subscriptionCreated`, `subscriptionRenewed`, `subscriptionTerminated`, `subscriptionSwitched`, `passCreated` and `passTerminated`.

**Source.** [API Caching](https://developers.cleeng.com/reference/api-caching): expiration, validation and invalidation. [Webhooks Configuration](https://developers.cleeng.com/docs/webhooks-configuration).

## ENT-05 Cached entitlements not re-checked within 24 hours

Severity: Low.

**Search:** the cache code found for ENT-04.

**Judge.** Confirmed when cached entitlements are used for longer than 24 hours without one live entitlement call for that customer on a play attempt.

**Why.** Cleeng counts entitlement calls as viewer engagement for churn prediction. Without them, the publisher's churn data is wrong.

**Fix.** Make at least one live entitlement call per customer per 24 hours, when the viewer tries to play. It can run in the background while playback starts from the cache.

**Source.** [Entitlements caching](https://developers.cleeng.com/docs/entitlements-caching): "send a request to one of API endpoints … that are counted as engagement at least once every 24 hours when a customer attempts to get access to content".
