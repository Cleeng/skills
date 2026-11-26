# SESS: sign-in and token refresh

## SESS-01 Sign-in where a token refresh would do

Severity: High.

**Search:**

```bash
rg -n -e '/auths\b' -e '/sso/auths' -e 'loginCustomer' -e 'generateCustomerToken' <scope>
rg -n -e 'refresh_token' -e 'refreshToken' <scope>
```

For each sign-in call site, find its callers: app start (`App`, `main`, `onCreate`, `onResume`, `applicationDidBecomeActive`, `init` of a Roku scene), route guards, HTTP interceptors, timers, and handlers for the identity provider's session renewal.

**Judge.**

- Confirmed: the codebase never calls `/auths/refresh_token` (and uses no widget or SDK that refreshes for it), but signs customers in.
- Confirmed: a sign-in runs on every app start, page load or request although a refresh token is stored or could be.
- Confirmed: a backend calls `/sso/auths` each time the identity provider renews its own session, with no change of identity.
- Likely: sign-in on a 401 from any Cleeng call, without trying a refresh first.
- Not a finding: sign-in after the user enters a password, after an identity-provider sign-in, or after a refresh fails with `401 AUTH0003`.

**Why.** Each needless sign-in costs Cleeng a lookup, a write and a new token. Cleeng throttles repeated sign-ins for the same account, so an app that signs in per request starts failing under load.

**Fix.**

```text
on app start, and when the JWT is within about 60 s of expiry:
  if a refresh token is stored:
    POST /auths/refresh_token { "refreshToken": <stored> }
      200 → store the new jwt AND the new refreshToken
      401 AUTH0003 → discard both, go to sign-in
      409 MSSDK0101 → another refresh is running: wait for it and use its result
  else:
    sign in (password, or POST /sso/auths from the backend after the identity provider signs the user in)
on sign-out: discard both tokens
```

**Source.** [Authorisation](https://developers.cleeng.com/docs/authorisation): "Check JWT validity and if it turns out that JWT has expired, call the /auths/refresh_token endpoint." [Implementing Mobile Apps](https://developers.cleeng.com/docs/payments_on_mobile_tv_apps_intro): "refresh token should be used with the Refresh token API to obtain fresh JWT".

## SESS-02 Rotated refresh token not stored

Severity: High.

**Search:**

```bash
rg -n -e 'refresh_token' <scope>
```

Read each response handler of `/auths/refresh_token` and the code that writes tokens to storage.

**Judge.**

- Confirmed: the handler stores `jwt` but not `refreshToken` from the response.
- Confirmed: the refresh token is written once at sign-in and never overwritten.
- Likely: the two tokens are stored in separate writes that can be interrupted between them (for example two async storage calls without awaiting both).

**Why.** Cleeng invalidates the refresh token on use. The next refresh fails with `401 AUTH0003`, and the app falls back to a full sign-in (SESS-01).

**Fix.** Store `jwt` and `refreshToken` from every refresh response, together.

```ts
const { jwt, refreshToken } = (await res.json()).responseData;
await tokenStore.save({ jwt, refreshToken });
```

**Source.** [Refresh token](https://developers.cleeng.com/reference/refresh-token): "Refresh token passed in request body will be invalidated. A new JWT and a new refresh token will be returned". [Authorisation](https://developers.cleeng.com/docs/authorisation): "It can be used only once and expires after that".

## SESS-03 Concurrent refresh calls

Severity: Medium.

**Search:**

```bash
rg -n -e 'refresh_token' -e 'refreshToken\(' -e 'Authenticator' -e 'interceptors' -e 'RequestInterceptor' <scope>
```

**Judge.**

- Confirmed: refresh starts from a per-request interceptor, an OkHttp `Authenticator`, an Alamofire `RequestInterceptor` or several components, with no shared in-flight promise, lock, mutex, actor or flag.
- Likely: several tabs or processes share one stored refresh token and each can refresh.
- Not a finding: one shared promise or lock, as in the MediaStore SDK and hosted widgets.

**Why.** The second concurrent refresh gets `409 MSSDK0101`. A client that treats that as failure signs the viewer out, and the viewer signs in again.

**Fix.** One refresh at a time per device. Share the in-flight call; on 409, wait for it and use its tokens.

```ts
let inflight: Promise<Tokens> | null = null;
export function refresh(): Promise<Tokens> {
  inflight ??= doRefresh().finally(() => { inflight = null; });
  return inflight;
}
```

```kotlin
private val refreshLock = Mutex()
suspend fun freshTokens(stale: String): Tokens = refreshLock.withLock {
    val current = store.load()
    if (current.jwt != stale) current else doRefresh(current.refreshToken).also(store::save)
}
```

**Source.** [Release Notes 2025.03.27](https://publisher.support.cleeng.com/hc/en-us/articles/19242044452636): "a new error (status 409) is sent if two or more requests come at the same time". [Refresh token](https://developers.cleeng.com/reference/refresh-token) error table: `409 MSSDK0101`.

## SESS-04 Refresh on a timer or before every call

Severity: Medium.

**Search:**

```bash
rg -n -e 'setInterval' -e 'setTimeout' -e 'Timer' -e 'scheduledTimer' -e 'postDelayed' -e 'WorkManager' -e 'schedule' <files that call refresh>
```

**Judge.**

- Confirmed: a timer refreshes on a fixed interval whether or not the app is in use.
- Confirmed: every API call refreshes first without reading `exp`.
- Not a finding: refresh when `exp` is near or passed, or once after a 401.

**Why.** Each needless refresh is a database write and a new token for Cleeng.

**Fix.** Read `exp` from the JWT locally (no signature check is needed for this in a client). Refresh when it is within about 60 seconds of expiry, or once after a 401.

**Source.** [Authorisation](https://developers.cleeng.com/docs/authorisation).

## SESS-05 Cleeng read used as a session check

Severity: Medium.

**Search:**

```bash
rg -n -e '/customers/' -e 'getCustomer' <scope>
rg -n -e '401' -e 'Unauthorized' -e 'isLogged' -e 'isAuthenticated' -e 'validateSession' <scope>
```

**Judge.** Confirmed when a call to `GET /customers/{id}` (or another Cleeng read) exists only to see whether it returns 401, and its body is ignored. Common in session middleware and app-start checks.

**Why.** Each check is a full API call that answers a question the JWT already answers.

**Fix.** Decide session validity locally from the JWT `exp` claim. Refresh when it has expired.

**Source.** Cleeng recommendation, following [Authorisation](https://developers.cleeng.com/docs/authorisation).

## SESS-06 Refresh errors handled wrongly

Severity: Medium.

**Search:**

```bash
rg -n -e 'AUTH0003' -e 'MSSDK0101' -e '409' <files that call refresh>
```

Read the error path of every refresh call.

**Judge.**

- Confirmed: a `401 AUTH0003` is retried.
- Confirmed: a `409 MSSDK0101` signs the viewer out or triggers a sign-in.
- Confirmed: a failed refresh is retried without limit.
- Likely: all refresh errors are treated alike.

**Why.** Each wrong branch turns a recoverable state into an extra sign-in or a loop.

**Fix.** `AUTH0003`: discard both tokens and go to sign-in. `MSSDK0101`: wait for the in-flight refresh and use its tokens. Network errors or 5xx: retry once after a delay, then keep the viewer signed in with the current JWT until it expires.

**Source.** [Refresh token](https://developers.cleeng.com/reference/refresh-token).

## SESS-07 Tokens kept after sign-out

Severity: Low.

**Search:**

```bash
rg -n -i -e 'logout' -e 'signout' -e 'sign_out' -e 'log_out' <scope>
rg -n -e 'refresh_tokens' -e 'cleeng\.logout' -e 'Auth\.logout' <scope>
```

**Judge.**

- Confirmed: sign-out leaves `jwt` or `refreshToken` in storage.
- Confirmed: the app uses hosted widgets or the MediaStore SDK and its sign-out does not call `window.cleeng.logout()` or `Auth.logout()`.
- Likely: a "sign out of all devices" feature does not call `DELETE /refresh_tokens`.

**Why.** A refresh token left on a shared device signs the next person in as the previous viewer for up to 100 days.

**Fix.** Clear both tokens, call the widget or SDK logout, and call `DELETE /refresh_tokens` for sign-out on all devices.

**Source.** [Cleeng hosted widgets: global communication methods](https://developers.cleeng.com/docs/cleeng-hosted-widgets-global-communication-methods): "when a user logs out from your main application, you should also programmatically log them out from the Cleeng widgets."
