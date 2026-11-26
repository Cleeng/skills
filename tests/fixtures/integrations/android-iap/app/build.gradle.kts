plugins {
    id("com.android.application")
    kotlin("android")
}

android {
    namespace = "com.acme.tv"
    compileSdk = 35
    defaultConfig {
        applicationId = "com.acme.tv"
        minSdk = 24
        buildConfigField("String", "MEDIASTORE_URL", "\"https://mediastoreapi.cleeng.com\"")
        buildConfigField("String", "INAPP_URL", "\"https://inapp.api.prod.cleeng.com\"")
        buildConfigField("String", "PUBLISHER_ID", "\"123456789\"")
    }
}

dependencies {
    implementation("com.android.billingclient:billing-ktx:7.1.1")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.9.0")
}
