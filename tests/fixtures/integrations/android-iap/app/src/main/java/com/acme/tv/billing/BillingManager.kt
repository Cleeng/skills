package com.acme.tv.billing

import com.acme.tv.BuildConfig
import com.acme.tv.auth.TokenStore
import com.android.billingclient.api.BillingClient
import com.android.billingclient.api.BillingResult
import com.android.billingclient.api.Purchase
import com.android.billingclient.api.PurchasesUpdatedListener
import kotlinx.coroutines.delay
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

class BillingManager(
    private val store: TokenStore,
    private val customerId: Long,
    private val ui: PurchaseUi,
) : PurchasesUpdatedListener {
    private val http = OkHttpClient()
    lateinit var billingClient: BillingClient

    override fun onPurchasesUpdated(result: BillingResult, purchases: MutableList<Purchase>?) {
        if (result.responseCode != BillingClient.BillingResponseCode.OK) return
        purchases?.forEach { purchase -> ui.launch { register(purchase) } }
    }

    private suspend fun register(purchase: Purchase) {
        val body = JSONObject()
            .put("cleengCustomerId", customerId)
            .put("purchaseToken", purchase.purchaseToken)
            .put("packageName", purchase.packageName)
            .put("productType", "subscription")
            .toString()
        val request = Request.Builder()
            .url("${BuildConfig.INAPP_URL}/google-play/purchases")
            .header("Authorization", "Bearer ${store.jwt}")
            .header("X-Publisher-Id", BuildConfig.PUBLISHER_ID)
            .post(body.toRequestBody("application/json".toMediaType()))
            .build()
        http.newCall(request).execute().use { res ->
            when (res.code) {
                202 -> waitForSync(JSONObject(res.body!!.string()).getString("synchronizationId"))
                409 -> ui.showError("This purchase could not be completed.")
                else -> ui.showError("Purchase failed (${res.code}).")
            }
        }
    }

    private suspend fun waitForSync(syncId: String) {
        while (true) {
            val request = Request.Builder()
                .url("${BuildConfig.INAPP_URL}/google-play/purchases/synchronizations/$syncId")
                .header("Authorization", "Bearer ${store.jwt}")
                .header("X-Publisher-Id", BuildConfig.PUBLISHER_ID)
                .build()
            val status = http.newCall(request).execute().use { JSONObject(it.body!!.string()).getString("status") }
            if (status == "SUCCEEDED") return ui.showSuccess()
            if (status == "FAILED") return ui.showError("Purchase could not be verified.")
            delay(1000)
        }
    }
}

interface PurchaseUi {
    fun launch(block: suspend () -> Unit)
    fun showSuccess()
    fun showError(message: String)
}
