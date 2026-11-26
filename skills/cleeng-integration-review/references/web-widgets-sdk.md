# WEB: hosted widgets and MediaStore SDK

## WEB-01 `cleeng.js` self-hosted or loaded repeatedly

Severity: Medium.

**Search:**

```bash
rg -n -e 'cleeng\.js' <client>
rg -n --files <client> | rg -i 'cleeng.*\.js$'
rg -n -e 'onAuthTokensUpdate' -e 'setAuthTokens' -e 'onWidgetEvent' <client>
```

**Judge.**

- Confirmed: a local copy of `cleeng.js` is served, or the script `src` is not `https://widgets.prod.cleeng.com/cleeng.js` (or the sandbox equivalent).
- Confirmed: the script tag is added from a component that renders more than once.
- Confirmed: `window.cleeng.onAuthTokensUpdate` or `onWidgetEvent` is registered inside a render path or an effect that re-runs, without cleanup.

**Why.** A self-hosted copy misses Cleeng's fixes. Registering listeners repeatedly duplicates token updates and events.

**Fix.** Load the script once in `<head>` from Cleeng's domain. Register the global methods once, at the top level of the app (for example `App.js`).

**Source.** [Checkout hosted widget](https://developers.cleeng.com/docs/checkout-hosted-widget): "Do not attempt to self-host cleeng.js script". [Cleeng hosted widgets: global communication methods](https://developers.cleeng.com/docs/cleeng-hosted-widgets-global-communication-methods): "Methods should be called only once in the entire application" and "calling it multiple times registers duplicate listeners".

## WEB-02 Tokens rotated by widgets or SDK not persisted

Severity: High.

**Search:**

```bash
rg -n -e 'onAuthTokensUpdate' -e 'setAuthTokens' -e 'setRefreshToken' -e 'setJWT' -e 'CLEENG_REFRESH_TOKEN' -e 'CLEENG_AUTH_TOKEN' <client>
```

**Judge.**

- Confirmed: the app passes tokens to the widgets or SDK but has no `onAuthTokensUpdate` handler that stores both new tokens.
- Confirmed: the app keeps its own copy of the refresh token and passes it again through `setAuthTokens` or `Config.setRefreshToken` after the widget or SDK may have rotated it.

**Why.** The widgets and the SDK refresh the JWT themselves, which rotates the refresh token. The app's stale copy then fails with `401 AUTH0003`, and the viewer has to sign in again (SESS-01).

**Fix.** Store both tokens from every `onAuthTokensUpdate` callback, and use only the latest pair.

```js
window.cleeng.onAuthTokensUpdate(({ jwt, refreshToken }) => tokenStore.save({ jwt, refreshToken }));
```

**Source.** [Cleeng hosted widgets: global communication methods](https://developers.cleeng.com/docs/cleeng-hosted-widgets-global-communication-methods).

## WEB-03 External SSO with profile or password editing in the Account widget

Severity: Medium.

**Search:**

```bash
rg -n -e 'data-cleeng-widget=.(account|updateProfile)' -e '<MyAccount' -e '<UpdateProfile' <client>
rg -n -e 'setAuthTokens' -e '/sso/auths' -e 'auth0' -e 'okta' -e 'cognito' -e 'firebase/auth' <scope>
```

**Judge.** Confirmed when the app signs viewers in through its own identity provider and also shows the Cleeng Account widget, `MyAccount` or `UpdateProfile` with profile and password editing available.

**Why.** Changes made in Cleeng drift from the identity provider's record, and a password set in Cleeng is not the one the viewer signs in with.

**Fix.** Hide profile and password editing in the Account widget. Set the Identity Provider option to External in the Cleeng dashboard.

**Source.** [Account hosted widget](https://developers.cleeng.com/docs/account-hosted-widget): "you must prevent users from editing their profiles or passwords within the Cleeng Account widget".

## WEB-04 No bot protection on register and purchase

Severity: Medium.

**Search:**

```bash
rg -n -e 'setGoogleRecaptcha' -e 'captchaValue' -e 'recaptcha' -e 'turnstile' -e 'hcaptcha' <client>
rg -n -e "/customers['\"\`]" -e '/orders' -e '<Register' -e '<Purchase' -e '<Checkout' <client>
```

**Judge.**

- Confirmed: the app registers customers or creates orders through MediaStore API or the MediaStore SDK directly, with no reCAPTCHA or other bot check.
- Not a finding: hosted widgets, which include Cleeng's own protection.

**Why.** Bots create accounts and test stolen cards through open register and purchase flows.

**Fix.** Enable reCAPTCHA on register and purchase (`Config.setGoogleRecaptcha` in the SDK, `captchaValue` on MediaStore calls), and match the setting in the Cleeng dashboard.

**Source.** [Fraud prevention solution with Google reCAPTCHA](https://developers.cleeng.com/docs/fraud-prevention-solution-with-google-recaptcha). [Enterprise Go Live Checklist](https://publisher.support.cleeng.com/hc/en-us/articles/4417301124252), item 25: "Ensure you have a captcha or other bot prevention mechanism implemented on your front-end application."
