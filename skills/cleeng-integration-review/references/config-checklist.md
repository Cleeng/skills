# Dashboard checklist

These settings live in the Cleeng dashboard or with Cleeng, so code cannot show them. Include the items that apply to the integration types found, as a checklist for the user.

## Every integration

- [ ] Production builds use production API keys; sandbox keys exist only in non-production configuration.
- [ ] Each API key is restricted to the IP addresses or ranges of the servers that use it.
- [ ] Each system or partner that calls Cleeng has its own API key, so a leaked or misbehaving key can be traced and replaced alone.
- [ ] Old or unused API keys are deleted.

## Webhooks

- [ ] Every webhook endpoint is registered through the Webhook Management API, with `retryPolicy` set.
- [ ] The signing secret is stored only in the receiving server's secret store, and rotated if it was ever exposed.
- [ ] Edge, CDN and WAF rules in front of the receiver let Cleeng's requests through.
- [ ] Payment-related topics and dunning action settings are configured before go-live.

## Web checkout and accounts

- [ ] Hosted widgets are restricted to the publisher's own domains.
- [ ] reCAPTCHA settings in the dashboard match the client configuration.
- [ ] With an external identity provider, the Identity Provider option is set to External.
- [ ] Public registration is turned off if viewers only sign up through the publisher's own identity provider.

## In-app purchases

- [ ] Store product ids are set on every Cleeng offer sold in an app store.
- [ ] Apple App Store Server Notifications and Google Play real-time developer notifications point at the In-App API URLs from the Cleeng dashboard.
- [ ] Cleeng has the store access it needs (for example the Google Play service account permission) after any app or account migration.

## Events and launches

- [ ] Cleeng knows about large live events or launches in advance, with the expected viewer numbers.
