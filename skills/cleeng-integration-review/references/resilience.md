# RES: timeouts, retries and 429

Start from the HTTP clients that call Cleeng: find where each is created and which options it gets.

```bash
rg -n -e 'axios\.create' -e 'new HttpClient' -e 'OkHttpClient' -e 'URLSession' -e 'requests\.Session' -e 'httpx\.' -e 'GuzzleHttp' -e 'got\.extend' -e 'ky\.create' -e 'fetch\(' -e 'roUrlTransfer' <files with Cleeng call sites>
```

## RES-01 No timeout on Cleeng calls

Severity: Medium.

**Search:**

```bash
rg -n -i -e 'timeout' -e 'AbortSignal' -e 'AbortController' -e 'timeoutInterval' -e 'callTimeout' -e 'readTimeout' -e 'SetMinimumTransferRate' <files with Cleeng clients>
```

**Judge.**

- Confirmed: a client that calls Cleeng has no timeout. Examples: `fetch` without an `AbortSignal`, axios or got without `timeout`, Python `requests` without `timeout=`, Guzzle without `timeout`.
- Confirmed: a timeout above 30 seconds on calls other than payments and in-app purchase registration.
- Not a finding: platform defaults that are already bounded when the code sets them explicitly (OkHttp's 10-second defaults, a `URLSessionConfiguration` with `timeoutIntervalForRequest`).

**Why.** A hung call holds a thread, a connection or a viewer's screen.

**Fix.** Set 8 seconds as the default for Cleeng calls. Payment and in-app purchase calls can take longer; give them their own, longer value.

```js
const cleeng = axios.create({ baseURL, timeout: 8000 });
// fetch
await fetch(url, { signal: AbortSignal.timeout(8000) });
```

**Source.** [Best Practices](https://developers.cleeng.com/reference/best-practices): "Set up a default timeout of 8 seconds."

## RES-02 Aggressive retries

Severity: High.

**Search:**

```bash
rg -n -e 'axios-retry' -e 'axiosRetry' -e 'retries' -e 'maxRetries' -e 'retry\(' -e 'tenacity' -e 'Retry\(' -e 'Polly' -e 'RetryPolicy' -e 'retryWhen' -e 'retryOnConnectionFailure' -e 'p-retry' <scope>
```

Also read hand-written loops around Cleeng calls: `for (let i = 0; i < n; i++)`, `while`, recursion on error.

**Judge.**

- Confirmed: retries on 4xx responses (400, 401, 403, 404, 409, 422). `retryCondition: () => true` and "retry on any error" count.
- Confirmed: retries with no delay between attempts.
- Confirmed: more than two retries on one Cleeng call.
- Confirmed: a retry loop around sign-in or customer lookup.
- Not a finding: one retry after a delay on network errors or 5xx, for reads.

**Why.** Retries multiply load while Cleeng is slow or scaling, which makes the slowdown longer. A 4xx never succeeds on retry.

**Fix.** Retry reads at most once, after a delay, on network errors and 5xx only. Never retry 4xx; handle 429 as in RES-03. Do not auto-retry writes (RES-04).

```js
axiosRetry(cleeng, {
  retries: 1,
  retryDelay: () => 1000,
  retryCondition: (e) => !e.response || e.response.status >= 500,
});
```

**Source.** [Best Practices](https://developers.cleeng.com/reference/best-practices): "Only retry failed API calls once, to avoid an uncontrolled cascade of requests."

## RES-03 429 not handled

Severity: Medium.

**Search:**

```bash
rg -n -e '429' -e 'MSSDK0002' -e 'Too many requests' -e 'Retry-After' -e 'TOO_MANY_REQUESTS' <scope>
```

**Judge.**

- Confirmed: a 429 is retried immediately.
- Likely: there is no branch for 429 or `MSSDK0002` anywhere, so a rate-limited viewer sees a generic error. Report this as Likely, with a note on which screens would break.

**Why.** Retrying a 429 at once keeps the viewer over the limit and lengthens the lockout. MediaStore's 429 does not send `Retry-After`.

**Fix.** On 429, wait before retrying: honour `Retry-After` when present, otherwise back off with jitter. Show cached data meanwhile.

**Source.** [How to Understand and Resolve Common API Errors (401, 429)](https://developers.cleeng.com/reference/how-to-understand-and-resolve-common-api-errors-401-429): "do not immediately retry the request. Implement an exponential backoff strategy … Use the Retry-After header if provided".

## RES-04 Writes retried without protection

Severity: Medium.

**Search:** the retry configuration found for RES-02, applied to:

```bash
rg -n -e 'post\(' -e "method:\s*['\"]POST" -e '\.post' -e 'POST' <files with Cleeng clients>
```

**Judge.** Confirmed when automatic retries cover `POST /orders`, payments, `POST /3.1/subscriptions`, `POST /customers` or `POST /purchases` without first checking whether the first attempt succeeded.

**Why.** Cleeng has no idempotency-key header. A retried write after a timeout can create a second order or subscription, or charge twice.

**Fix.** Exclude writes from automatic retries. After a timeout on a write, read the current state (order, subscription) before trying again. In-app purchase registration is the exception: follow IAP-02.

**Source.** [Reference materials](https://developers.cleeng.com/docs/reference-materials): "requests made by connector should be idempotent. This serves to avoid sending multiple requests and overcharging a user."

## RES-05 One circuit breaker for every Cleeng call

Severity: Low.

**Search:**

```bash
rg -n -i -e 'circuit' -e 'breaker' -e 'opossum' -e 'resilience4j' -e 'Polly' -e 'pybreaker' <scope>
```

**Judge.** Confirmed when one breaker wraps the whole Cleeng client, so failures on one endpoint stop sign-in, checkout and playback together.

**Why.** One slow endpoint should not block unrelated flows.

**Fix.** Use one breaker per endpoint group: sign-in and refresh, entitlements, account reads, payments. While the entitlement breaker is open, serve the cached `accessGranted`.

**Source.** Cleeng recommendation.
