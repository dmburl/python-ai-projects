package com.dmburl.pic2text

import android.util.Base64
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException

object NetworkClient {

    private val client = OkHttpClient()

    suspend fun sendImageToGenerativeApi(apiKey: String, model: String, imageBytes: ByteArray, mimeType: String): String {
        return withContext(Dispatchers.IO) {
            val base64Image = Base64.encodeToString(imageBytes, Base64.NO_WRAP)

            val jsonBody = JSONObject().apply {
                put("contents", JSONArray().apply {
                    put(JSONObject().apply {
                        put("parts", JSONArray().apply {
                            put(JSONObject().apply {
                                put("text", "Transcribe this image to Markdown")
                            })
                            put(JSONObject().apply {
                                put("inline_data", JSONObject().apply {
                                    put("mime_type", mimeType)
                                    put("data", base64Image)
                                })
                            })
                        })
                    })
                })
            }

            val requestBody = jsonBody.toString().toRequestBody("application/json".toMediaType())

            val url = "https://generativelanguage.googleapis.com/v1beta/models/$model:generateContent?key=$apiKey"

            val request = Request.Builder()
                .url(url)
                .post(requestBody)
                .build()

            client.newCall(request).execute().use { resp ->
                if (!resp.isSuccessful) throw IOException("Unexpected code ${resp.code} ${resp.body?.string()}")
                // This is a basic parser, for a production app you'll want to use a JSON parsing library
                val responseBody = resp.body?.string()
                if (responseBody != null) {
                    try {
                        val jsonResponse = JSONObject(responseBody)
                        val candidates = jsonResponse.getJSONArray("candidates")
                        if (candidates.length() > 0) {
                            val firstCandidate = candidates.getJSONObject(0)
                            val content = firstCandidate.getJSONObject("content")
                            val parts = content.getJSONArray("parts")
                            if (parts.length() > 0) {
                                return@withContext parts.getJSONObject(0).getString("text")
                            }
                        }
                    } catch (e: Exception) {
                        throw IOException("Error parsing JSON response: ${e.message}")
                    }
                }
                "Error: Could not parse response"
            }
        }
    }
}
