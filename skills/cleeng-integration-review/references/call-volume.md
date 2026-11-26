# LOAD: call volume and caching

## LOAD-02 Account data read on every screen

Severity: High.

**Search** in `<client>` folders, and in `<server>` folders that proxy account data:

```bash
rg -n -e '/customers/' -e '/subscriptions' -e '/passes' -e '/payment_details' -e '/transactions' <scope>
rg -n -e 'useEffect' -e 'componentDidMount' -e 'onMounted' -e 'loader' -e 'onAppear' -e 'viewDidAppear' -e 'onResume' -e 'onCreateView' <files with those calls>
```

**Judge.**

- Confirmed: the customer profile, subscriptions, passes or payment details are fetched in a component mount, page loader, render path or per-request middleware with no cache, store or memo in between, so each navigation repeats the call.
- Confirmed: payment details are read outside the account and payment screens.
- Likely: a shared store exists but is cleared on every navigation.
- Not a finding: one read after sign-in kept in app state (Redux, Zustand, a ViewModel, a singleton), refreshed after a purchase, cancellation or plan change and on the account screen.

**Why.** The same data comes back on every screen, and each read counts towards the viewer's per-endpoint limit.

**Fix.** Read the profile, passes and subscriptions once after sign-in and keep them in app state for the session. Read them again after a purchase, cancellation or plan change made in the app, and when the viewer opens the account screen. Read payment details only on the payment screen. On a 5xx, retry once after a delay, then show the cached data.

**Source.** [API Caching](https://developers.cleeng.com/reference/api-caching): "we suggest implementing caching to the following resources: Entitlements … Customer data … Offers". [Getting Started](https://developers.cleeng.com/reference/getting-started): MediaStore rate limit.

## LOAD-03 Customer looked up by email on each request

Severity: High.

**Search** in `<server>` folders:

```bash
rg -n -e 'customers\?email' -e "customers['\"\`]?\s*,\s*\{\s*params" -e 'listCustomerSubscriptions' -e 'isTrialAllowed' -e 'generateCustomerToken' -e 'customerEmail' <server>
```

**Judge.**

- Confirmed: a request handler, middleware or job looks up the Cleeng customer by email every time it runs, and no customer id is stored for the user.
- Likely: the id is cached in memory per process only, so each instance and restart repeats lookups.
- Not a finding: the lookup runs once to link an account, and the id is then stored beside the integrator's own user record.

**Why.** A Cleeng customer id never changes once the account exists, so repeated lookups return the same answer. An email can also match more than one Cleeng record (for example a guest and a registered customer), which makes email lookups less reliable than ids.

**Fix.** Store the Cleeng customer id beside the integrator's own user id after the first lookup, or read `customerId` from a verified Cleeng JWT (AUTH-03). Look up by email only when no id is stored, or when a stored id returns 404.

**Source.** [List customers](https://developers.cleeng.com/reference/list-customers). Storing the id is a Cleeng recommendation.

## LOAD-04 Email lookup built wrongly

Severity: Medium.

**Search:**

```bash
rg -n -e 'email=' -e "email['\"]?\s*:" <server>
```

**Judge.**

- Confirmed: the email goes into the query string by concatenation or interpolation without `encodeURIComponent`, `URLEncoder.encode`, `urlencode`, `addingPercentEncoding` or the HTTP client's params option.
- Confirmed: the lookup omits `limit=1` when it only checks whether an account exists.

**Why.** An unencoded `+` in an email becomes a space. The lookup misses, and code that then tries to create the customer can loop.

**Fix.**

```js
await core.get("/3.1/customers", { params: { email, limit: 1 } }); // the HTTP client encodes params
```


**Source.** [List customers](https://developers.cleeng.com/reference/list-customers): "The recommended limit for checking if a user is registered using an email address is: 1." and "Email must be URL-encoded."

## LOAD-05 Cleeng polled on a timer

Severity: High.

**Search:**

```bash
rg -n -e 'setInterval' -e 'setTimeout' -e 'Timer' -e 'scheduledTimer' -e 'postDelayed' -e 'repeatOnLifecycle' -e 'while\s*\(\s*true' -e 'cron' -e '@Scheduled' -e 'schedule\.' -e 'roSGNode.*Timer' <scope>
```

Keep hits that call Cleeng, directly or through a helper.

**Judge.**

- Confirmed: a timer calls Cleeng per viewer: entitlement re-checks during playback, subscription status polls, heartbeats, access checks in every open tab.
- Confirmed: a scheduled job calls Cleeng once per customer on each run to detect subscription or access changes.
- Not a finding: the bounded in-app purchase sync poll (IAP-03), or one retry after a failure.

**Why.** Polling traffic grows with concurrent viewers divided by the interval, whether or not anything changed. A poll every 9 seconds uses a viewer's whole MediaStore allowance for that endpoint.

**Fix.** Check access when playback starts. Learn about subscription changes from webhooks in the backend, and keep a reconciliation job that runs daily or less often. For in-app purchase sync, use the bounded poll in IAP-03.

**Source.** [Getting Started](https://developers.cleeng.com/reference/getting-started): "about 1 request every 9 seconds on average". [API Caching](https://developers.cleeng.com/reference/api-caching).

## LOAD-06 Checkout mounted for viewers who already have access

Severity: Medium.

**Search** in `<client>` folders:

```bash
rg -n -e 'data-cleeng-widget=.checkout' -e '<Checkout' -e '<Purchase' -e 'cleengSection=checkout' <client>
```

**Judge.** Confirmed when the checkout widget or component renders on content pages for every viewer, with no entitlement check before it.

**Why.** Each mount loads offers, payment methods and session data for a viewer who will not buy.

**Fix.** Check the cached entitlement first, and render checkout only for viewers without access.

**Source.** [Externally managed passes](https://developers.cleeng.com/docs/externally-managed-passes): "We recommended that your client app checks entitlements before allowing a user to purchase a pass."

## LOAD-07 Static data fetched per request

Severity: Low.

**Search:**

```bash
rg -n -e 'payment-methods' -e 'payment_methods' -e '/offers' <scope>
```

**Judge.**

- Confirmed: payment methods are fetched on every checkout only to find a `paymentMethodId`.
- Likely: offer details are fetched on every page view without a cache.

**Why.** Payment method ids are constant, and offers change rarely.

**Fix.** Hard-code the `paymentMethodId` values the app uses. Cache offer details for a few minutes.

**Source.** [Payment information](https://developers.cleeng.com/docs/payment-information): "It is recommended to use hardcoded paymentMethodId to decrease the number of requests". [API Caching](https://developers.cleeng.com/reference/api-caching).

## LOAD-08 Load tests or unthrottled bulk jobs against Cleeng

Severity: Medium.

**Search:**

```bash
rg -n -i -e 'cleeng' -g '*k6*' -g '*.jmx' -g '*locust*' -g '*artillery*' -g '*gatling*' -g '*.js' -g '*.py' -g '*.scala' -g '*.yml' <test and script folders>
rg -n -e 'Promise\.all' -e 'ThreadPoolExecutor' -e 'asyncio\.gather' -e 'parallelStream' -e 'DispatchQueue\.concurrentPerform' <files that call Cleeng>
```

**Judge.**

- Confirmed: a load-test script or config targets a Cleeng host, sandbox included.
- Confirmed: an import, sync or migration script calls Cleeng over a list of customers with unbounded concurrency.
- Not a finding: load tests that target a mock of Cleeng.

**Why.** Cleeng may throttle or block traffic that looks like a spike or a scan.

**Fix.** Mock Cleeng in load tests, and agree any test against Cleeng hosts with Cleeng first. Throttle bulk jobs to 100 requests per second or less, and tell Cleeng 48 hours ahead when loading 5,000 users or more.

**Source.** [Load testing](https://developers.cleeng.com/docs/load-testing-online-video-platform): "Load testing directly on Cleeng's production or sandbox environments is strictly NOT allowed". [Migrating to Cleeng](https://developers.cleeng.com/docs/migrating-to-cleeng): "Throttle at 100 RPS for migrations to avoid any risks."
