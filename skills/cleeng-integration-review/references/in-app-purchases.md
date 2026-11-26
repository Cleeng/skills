# IAP: in-app purchases

Find purchase code first:

```bash
rg -n -e 'StoreKit' -e 'Transaction\.updates' -e 'BillingClient' -e 'onPurchasesUpdated' -e 'queryPurchasesAsync' -e 'roChannelStore' -e 'PurchasingService' -e '/purchases' -e 'purchase-validation' -e 'purchase-status' -e 'inapp\.api' <scope>
```

## IAP-01 Store transactions not all registered with Cleeng

Severity: High.

**Search:** the purchase code, then:

```bash
rg -n -e 'queryPurchasesAsync' -e 'Transaction\.updates' -e 'Transaction\.currentEntitlements' -e 'AppStore\.sync' -e 'restore' <client>
```

**Judge.**

- Confirmed: `POST …/purchases` is sent only from the initial purchase callback. Renewals and restores never reach Cleeng.
- Confirmed: an Android app never calls `queryPurchasesAsync()` on launch or resume to re-submit purchases Cleeng has not processed.
- Confirmed: an iOS/tvOS app does not listen to `Transaction.updates` or does not register restored transactions.
- Likely: the purchase button works before the viewer is signed in to Cleeng.

**Why.** A transaction Cleeng never receives lands on an "Unidentified User", and the paying viewer gets no access.

**Fix.** Sign the viewer in before purchase. Register initial purchases, renewals and restores. On Android, call `queryPurchasesAsync()` on every launch and re-submit unprocessed purchases. On Apple platforms, process `Transaction.updates` and restored transactions.

**Source.** [Understanding Unidentified Users in In-App Purchases](https://publisher.support.cleeng.com/hc/en-us/articles/27688710570652): "This must include initial purchases, subscription renewals, and purchase restorations." [Google Play Billing](https://developers.cleeng.com/docs/google-play-billing): "on every app launch, call BillingClient.queryPurchasesAsync() and re-submit any unprocessed purchases".

## IAP-02 Purchase sync responses mishandled

Severity: Medium.

**Search:**

```bash
rg -n -e '409' -e 'RESOURCE_TEMPORARY_LOCKED_FOR_PROCESSING' -e 'SK2C0101' -e 'RECEIVED_EXPIRED_PURCHASE' -e 'synchronizationId' -e 'Correlation-Id' <scope>
```

**Judge.**

- Confirmed: a 409 from purchase registration is shown as a failure, or the purchase is posted again.
- Confirmed: `RECEIVED_EXPIRED_PURCHASE` is retried. Other 4xx retries are RES-02.
- Confirmed: `Correlation-Id` is a constant.

**Why.** A 409 means Cleeng is already processing that purchase. Posting it again adds load and can show the viewer a false failure. A 400 or 422 never succeeds on retry.

**Fix.** On 409, take `synchronizationId` from the response and resume polling (IAP-03). Do not retry 400, 422 or expired purchases; ask the viewer to buy again for an expired purchase. Send a unique `Correlation-Id` per purchase.

**Source.** [Google Play Billing](https://developers.cleeng.com/docs/google-play-billing): "Not an error - extract synchronizationId from the response and resume polling." and "Do not retry."

## IAP-03 Unbounded purchase-sync polling

Severity: Medium.

**Search:**

```bash
rg -n -e 'synchronizations' -e 'purchase-status' <scope>
```

Read the loop around each hit.

**Judge.**

- Confirmed: the poll has no overall time limit or attempt cap.
- Confirmed: it polls more often than every 2 seconds.

**Why.** Twenty polls already equal the MediaStore burst allowance for one customer on one endpoint, and an unbounded poll never stops for a purchase Cleeng cannot sync.

**Fix.** Poll every 3 seconds for up to 60 seconds. After that, rely on the `inappPurchaseSyncResult` webhook or an entitlement check, and tell the viewer the purchase is being processed. Grant temporary access meanwhile if the app supports it.

**Source.** [Apple In-App Purchase (StoreKit 2)](https://developers.cleeng.com/docs/apple-in-app-purchase-storekit-2). [Google Play Billing](https://developers.cleeng.com/docs/google-play-billing).

## IAP-04 Duplicate purchase not prevented

Severity: Medium.

**Search:** the code that shows purchase buttons or offers in the app.

**Judge.**

- Confirmed: purchase options show without checking the viewer's entitlement or a pending validation.
- Likely: `correlationId` from the purchase is not stored on the device after each purchase (Apple passes).
- Likely: offers without a store product id are shown.

**Why.** Viewers buy the same subscription twice and ask for refunds, or try to buy an offer the store cannot sell.

**Fix.** Before showing purchase options, check the entitlement and any pending validation. Store `correlationId` after each purchase. Show only offers with a store product id that the viewer does not own.

**Source.** [Apple In-App Purchase (StoreKit 2)](https://developers.cleeng.com/docs/apple-in-app-purchase-storekit-2): "the client app should make sure there is no pending validation and no active entitlement to an offer before allowing the user to purchase". [Implementing Mobile Apps](https://developers.cleeng.com/docs/payments_on_mobile_tv_apps_intro).

## IAP-05 Deprecated in-app endpoints

Severity: Medium.

**Search:**

```bash
rg -n -e '/apple/payment' -e '/android/payment' -e '/roku/payment' -e 'storekit2/purchase-validation' -e 'storekit2/purchase-status' -e 'notification\.cleeng\.com' -e 'subscriptions/transfers/(apple|android)' -e '/receipt/' <scope>
```

**Judge.** Confirmed on any hit in code that runs.

**Why.** These endpoints are deprecated. StoreKit 1 endpoints were deprecated on 9 October 2025.

**Fix.** Move to the In-App API on `inapp.api.prod.cleeng.com`: StoreKit 2 (`POST /storekit2/purchases`) and the Google Play Billing Connector V2 (`POST /google-play/purchases`), with the matching synchronizations and transfers endpoints.

**Source.** [Android](https://developers.cleeng.com/docs/android): "We recommend using our new Google Play Billing Connector V2". [Apple In-App Purchase (StoreKit 2)](https://developers.cleeng.com/docs/apple-in-app-purchase-storekit-2).

## IAP-06 Missing `X-Publisher-Id` on In-App API calls

Severity: Low.

**Search:** each call to `inapp.api.*`, then:

```bash
rg -n -i -e 'x-publisher-id' <files with In-App API calls>
```

**Judge.**

- Confirmed: an In-App API call has no `X-Publisher-Id` header. A missing `ipAddress` on server-side calls is AUTH-05.

**Why.** Requests without `X-Publisher-Id` are rejected.

**Fix.** Send `X-Publisher-Id` on every In-App API call.

**Source.** [Google Play Billing](https://developers.cleeng.com/docs/google-play-billing): "Always include the X-Publisher-Id header."
