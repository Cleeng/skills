package com.acme.tv.auth

import com.acme.tv.BuildConfig
import okhttp3.Authenticator
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import okhttp3.Route
import org.json.JSONObject

class TokenAuthenticator(private val store: TokenStore) : Authenticator {
    private val client = OkHttpClient()

    override fun authenticate(route: Route?, response: Response): Request? {
        val body = JSONObject().put("refreshToken", store.refreshToken).toString()
        val refresh = Request.Builder()
            .url("${BuildConfig.MEDIASTORE_URL}/auths/refresh_token")
            .post(body.toRequestBody("application/json".toMediaType()))
            .build()
        client.newCall(refresh).execute().use { res ->
            if (!res.isSuccessful) return null
            val data = JSONObject(res.body!!.string()).getJSONObject("responseData")
            store.jwt = data.getString("jwt")
            store.refreshToken = data.getString("refreshToken")
        }
        return response.request.newBuilder()
            .header("Authorization", "Bearer ${store.jwt}")
            .build()
    }
}
