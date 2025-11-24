package com.dmburl.pic2text

import android.content.Context
import android.content.SharedPreferences
import android.net.Uri
import android.os.Bundle
import android.provider.DocumentsContract
import android.provider.OpenableColumns
import android.util.Log
import android.widget.ArrayAdapter
import android.widget.AutoCompleteTextView
import android.widget.Button
import android.widget.ProgressBar
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import com.google.android.material.progressindicator.LinearProgressIndicator
import com.google.android.material.textfield.TextInputEditText
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.IOException
import java.io.InputStream

class MainActivity : AppCompatActivity() {

    private lateinit var editApiKey: TextInputEditText
    private lateinit var btnSaveKey: Button
    private lateinit var spinnerModel: AutoCompleteTextView
    private lateinit var btnPickImages: Button
    private lateinit var tvSelectedCount: TextView
    private lateinit var btnPickOutputDir: Button
    private lateinit var tvOutputDir: TextView
    private lateinit var progressBar: LinearProgressIndicator
    private lateinit var btnStart: Button

    private var selectedUris: List<Uri> = emptyList()
    private var outputDirUri: Uri? = null

    private val pickImages = registerForActivityResult(ActivityResultContracts.OpenMultipleDocuments()) { uris ->
        if (uris != null) {
            selectedUris = uris
            tvSelectedCount.text = "${uris.size} file(s) selected"
        }
    }

    private val pickOutputDirLauncher = registerForActivityResult(ActivityResultContracts.OpenDocumentTree()) { uri ->
        uri?.let {
            outputDirUri = it
            tvOutputDir.text = "Output to: ${it.path}"
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        editApiKey = findViewById(R.id.edit_api_key)
        btnSaveKey = findViewById(R.id.btn_save_key)
        spinnerModel = findViewById(R.id.spinner_model)
        btnPickImages = findViewById(R.id.btn_pick_images)
        tvSelectedCount = findViewById(R.id.tv_selected_count)
        btnPickOutputDir = findViewById(R.id.btn_pick_output_dir)
        tvOutputDir = findViewById(R.id.tv_output_dir)
        progressBar = findViewById(R.id.progressBar)
        btnStart = findViewById(R.id.btn_start)

        // prefill saved key if any
        lifecycleScope.launch {
            readApiKey()?.let { editApiKey.setText(it) }
        }

        val models = arrayOf("gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-pro", "gemini-1.5-flash")
        val adapter = ArrayAdapter(this, android.R.layout.simple_dropdown_item_1line, models)
        spinnerModel.setAdapter(adapter)

        btnSaveKey.setOnClickListener {
            val key = editApiKey.text.toString().trim()
            if (key.isNotEmpty()) {
                lifecycleScope.launch {
                    saveApiKey(key)
                    editApiKey.setText("")
                    editApiKey.hint = "Key saved"
                }
            }
        }

        btnPickImages.setOnClickListener {
            // allow images and PDFs
            pickImages.launch(arrayOf("image/*", "application/pdf"))
        }

        btnPickOutputDir.setOnClickListener {
            pickOutputDirLauncher.launch(null)
        }

        btnStart.setOnClickListener {
            lifecycleScope.launch {
                val apiKey = readApiKey()
                if (apiKey.isNullOrBlank()) {
                    editApiKey.hint = "Please enter your API key and save it"
                    return@launch
                }

                if (selectedUris.isEmpty()) {
                    tvSelectedCount.text = "No files selected"
                    return@launch
                }

                if (outputDirUri == null) {
                    tvOutputDir.text = "Please select an output directory"
                    return@launch
                }

                val selectedModel = spinnerModel.text.toString()
                processFiles(apiKey, selectedModel, selectedUris, outputDirUri!!)
            }
        }
    }

    private suspend fun getEncryptedPrefs(context: Context): SharedPreferences = withContext(Dispatchers.IO) {
        val masterKey = MasterKey.Builder(context.applicationContext)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()

        EncryptedSharedPreferences.create(
            context.applicationContext,
            "secure_prefs",
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }

    private suspend fun saveApiKey(apiKey: String) {
        val prefs = getEncryptedPrefs(this)
        withContext(Dispatchers.IO) {
            prefs.edit().putString("GEMINI_API_KEY", apiKey).apply()
        }
    }

    private suspend fun readApiKey(): String? {
        val prefs = getEncryptedPrefs(this)
        return withContext(Dispatchers.IO) {
            prefs.getString("GEMINI_API_KEY", null)
        }
    }

    private fun processFiles(apiKey: String, model: String, uris: List<Uri>, outputDirUri: Uri) {
        progressBar.progress = 0
        val scope = CoroutineScope(Job() + Dispatchers.Main)
        scope.launch {
            val total = uris.size
            var success = 0

            val dirDocUri = DocumentsContract.buildDocumentUriUsingTree(outputDirUri, DocumentsContract.getTreeDocumentId(outputDirUri))

            for ((i, uri) in uris.withIndex()) {
                val fileName = getFileName(uri) ?: "Unknown File"
                updateStatus("Processing ${i + 1}/$total: $fileName")
                try {
                    val (bytes, mimeType) = withContext(Dispatchers.IO) { uriToBytes(uri) }
                    val md = NetworkClient.sendImageToGenerativeApi(apiKey, model, bytes, mimeType)
                    val outputFileName = fileName.substringBeforeLast('.') + ".md"

                    val newFileUri = DocumentsContract.createDocument(contentResolver, dirDocUri, "text/markdown", outputFileName)

                    newFileUri?.let {
                        contentResolver.openOutputStream(it)?.use { outputStream ->
                            outputStream.write(md.toByteArray())
                        }
                    }
                    Log.d("Pic2Text", "Got md: ${md.take(120)}")
                    success++
                } catch (e: Exception) {
                    Log.e("Pic2Text", "Error processing file", e)
                }
                progressBar.progress = ((i + 1) * 100) / total
            }
            updateStatus("Done: $success/$total processed.")
        }
    }

    private fun updateStatus(text: String) {
        runOnUiThread { tvSelectedCount.text = text }
    }

    private fun uriToBytes(uri: Uri): Pair<ByteArray, String> {
        val cr = contentResolver
        val mime = cr.getType(uri) ?: "image/jpeg"
        cr.openInputStream(uri).use { input: InputStream? ->
            val bytes = input!!.readBytes()
            return Pair(bytes, mime)
        }
    }

    private fun getFileName(uri: Uri): String? {
        var name: String? = null
        contentResolver.query(uri, null, null, null, null)?.use { cursor ->
            val nameIndex = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
            if (nameIndex >= 0 && cursor.moveToFirst()) {
                name = cursor.getString(nameIndex)
            }
        }
        return name
    }
}
