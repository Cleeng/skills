package com.acme.tv.auth

import android.content.SharedPreferences

class TokenStore(private val prefs: SharedPreferences) {
    var jwt: String?
        get() = prefs.getString("jwt", null)
        set(value) = prefs.edit().putString("jwt", value).apply()

    var refreshToken: String?
        get() = prefs.getString("refresh", null)
        set(value) = prefs.edit().putString("refresh", value).apply()
}
