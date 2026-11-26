# HOOK: webhooks

Find receivers first:

```bash
rg -n -e 'broadcasterId' -e 'X-Webhook' -e 'x-webhook' -e 'subscriptionCreated' -e 'subscriptionTerminated' -e 'webhook' <server>
```

## HOOK-01 Webhook signature not verified

Severity: Critical.

**Search:**

```bash
rg -n -i -e 'x-webhook-signature' -e 'createHmac' -e 'hmac' -e 'HMAC' <server>
```

**Judge.**

- Confirmed: a handler that processes Cleeng topics never reads `X-Webhook-Signature`.
- Confirmed: the signature is read but a failed check does not stop processing.
- Not a finding: verification in a middleware the handler's route uses. Follow the route definition.

**Why.** Anyone who finds the URL can post `subscriptionCreated` and grant access, or post `subscriptionTerminated` and remove it.

**Fix.** Compute the base64 HMAC-SHA256 of the raw request body with the endpoint's signing secret, and compare it with the header in constant time (HOOK-02). Answer 401 when it does not match.

**Source.** [Webhooks Configuration](https://developers.cleeng.com/docs/webhooks-configuration): "you must verify their signature. This is the most critical security step."

## HOOK-02 Webhook signature computed wrongly

Severity: High.

**Search:** the HMAC code found for HOOK-01, then:

```bash
rg -n -e 'JSON\.stringify\(req\.body' -e 'json\.dumps' -e 'json_encode' -e 'sha512' -e 'SHA512' -e 'hexdigest' -e "digest\(['\"]hex" <server>
rg -n -e '===' -e '!==' -e '==' <files with HMAC code>
```

**Judge.**

- Confirmed: the HMAC covers re-serialized JSON (`JSON.stringify(req.body)`, `json.dumps(request.json)`) instead of the raw bytes received.
- Confirmed: the comparison uses `==`, `===`, `!==`, `equals` or string comparison.
- Confirmed: the digest is hex or SHA-512. Cleeng sends base64 HMAC-SHA256.

**Why.** Re-serialized JSON can differ from the bytes Cleeng signed, so valid events fail. A plain comparison leaks timing.

**Fix.**

```js
app.post("/webhooks/cleeng", express.raw({ type: "application/json" }), (req, res) => {
  const expected = crypto.createHmac("sha256", process.env.CLEENG_WEBHOOK_SECRET).update(req.body).digest("base64");
  const given = req.get("X-Webhook-Signature") ?? "";
  const ok = given.length === expected.length && crypto.timingSafeEqual(Buffer.from(given), Buffer.from(expected));
  if (!ok) return res.sendStatus(401);
  // parse JSON.parse(req.body) after verification
});
```

Python: `hmac.compare_digest`. PHP: `hash_equals`. Go: `hmac.Equal`. Java/Kotlin: `MessageDigest.isEqual`.

**Source.** [Webhooks Configuration](https://developers.cleeng.com/docs/webhooks-configuration): verify over the raw body, "do NOT parse then re-serialize", use a constant-time comparison.

## HOOK-03 Webhook handler not idempotent

Severity: Medium.

**Search:**

```bash
rg -n -i -e 'x-webhook-delivery-id' -e 'deliveryId' -e 'delivery_id' <server>
```

**Judge.**

- Confirmed: nothing de-duplicates on `X-Webhook-Delivery-Id`, and the handler has effects that must not repeat: extending access, sending emails, counting renewals.
- Not a finding: handlers whose effects are naturally idempotent (setting a status to a given value).

**Why.** Cleeng retries a delivery with the same delivery id. A handler that grants, extends or emails twice corrupts state.

**Fix.** Record processed delivery ids, for example in a table with a unique key, and skip repeats.

**Source.** [Webhooks Configuration](https://developers.cleeng.com/docs/webhooks-configuration): "implement idempotency using the X-Webhook-Delivery-Id header".

## HOOK-04 Transient webhook failures answered with 4xx, or slow handlers

Severity: High.

**Search:** the receiver handlers, then:

```bash
rg -n -e 'status\(4' -e 'sendStatus\(4' -e 'abort\(4' -e 'HttpStatus\.(BAD_REQUEST|NOT_FOUND|CONFLICT|FORBIDDEN)' -e 'return 4[0-9][0-9]' <webhook handler files>
rg -n -i -e 'retryPolicy' -e '/endpoints' <server>
rg -n -i -e 'Cleeng Webhook Engine' -e 'user-agent' <edge, WAF, CDN or nginx config>
```

**Judge.**

- Confirmed: the handler answers 4xx for errors that can clear on a retry: database or queue unavailable, customer not yet known locally, a lock held.
- Confirmed: endpoints are registered through the Webhook Management API without `retryPolicy`.
- Likely: the handler does slow work (HTTP calls, emails) before answering, with no queue.
- Likely: an edge, WAF or bot rule in the repository could block Cleeng's requests.

**Why.** Cleeng treats any 4xx as a permanent failure and does not retry it. Without `retryPolicy` there is a single attempt. A lost `subscriptionTerminated` leaves access open; a lost `subscriptionCreated` leaves a paying viewer locked out.

**Fix.** Verify, enqueue and answer 2xx within a few seconds. Answer 5xx for transient errors so Cleeng retries. Register endpoints with `retryPolicy`. Run a periodic reconciliation job as a safety net.

**Source.** [Webhooks Configuration](https://developers.cleeng.com/docs/webhooks-configuration): "A delivery is considered permanently failed if it exhausts all retry attempts or if your endpoint returns a 4xx status code." [How to create add-on offers](https://developers.cleeng.com/docs/how-to-create-add-on-offers): "webhooks may not always be delivered - we recommend running the periodic script as a safety net."

## HOOK-05 Removed webhook API or topic

Severity: High.

**Search:**

```bash
rg -n -e 'webhook_subscriptions' -e 'subscribeToWebhookEvent' -e 'subscriptionReadyForTermination' <scope>
```

**Judge.** Confirmed on any hit in code that runs (not in comments or changelogs).

**Why.** `PUT /3.1/webhook_subscriptions/{topic}`, `GET /3.1/webhook_subscriptions` and webhook filtering were removed on 9 April 2026. The `subscriptionReadyForTermination` topic was removed on 23 April 2026. Code that uses them no longer works.

**Fix.** Register endpoints with the Webhook Management API at `https://webhook.api.prod.cleeng.com/` (`POST /endpoints`). Handle `subscriptionTerminated` instead of `subscriptionReadyForTermination`.

**Source.** [Release Notes 2026.04.09](https://publisher.support.cleeng.com/hc/en-us/articles/26673178605852): "Stop using the legacy PUT /webhook_subscriptions/{topic} endpoint".
