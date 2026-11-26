package com.acme.tv.legacy

import com.acme.tv.BuildConfig
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

// Kept for app versions released before the billing migration.
object LegacyPayment {
    private val http = OkHttpClient()

    fun submit(jwt: String, offerId: String, receipt: JSONObject) {
        val body = JSONObject().put("offerId", offerId).put("receipt", receipt).toString()
        val request = Request.Builder()
            .url("${BuildConfig.MEDIASTORE_URL}/android/payment")
            .header("Authorization", "Bearer $jwt")
            .post(body.toRequestBody("application/json".toMediaType()))
            .build()
        http.newCall(request).execute().close()
    }
}
