# android-pic2text-app

This folder contains a starter Android Studio Kotlin project scaffold to port `Picture2text/ocr2md.py` into an Android app.

Goal
- Let the end user provide their own Google Gemini API key and store it securely on-device using EncryptedSharedPreferences.
- Allow the user to pick images (or PDFs) and convert them to Markdown via the Generative API.

What I scaffolded
- Basic Android Studio project layout under `android-pic2text-app/` (module `app`).
- `MainActivity` with UI for entering/saving API key, picking images, and starting processing.
- A small `NetworkClient` helper (OkHttp + coroutine) with a placeholder endpoint — replace with the exact Google Generative API endpoint/payload.
- `EncryptedSharedPreferences` usage for secure on-device storage of the user-supplied API key.

Important notes
- This is a starter skeleton. Android Studio will generate or update Gradle wrapper files and may require updating plugin versions depending on your local environment.
- Do NOT hardcode API keys in the app. This scaffold stores user-supplied keys encrypted on device; clearing app data removes them.
- Replace the placeholder Generative API endpoint and payload in `NetworkClient.kt` with the exact REST call required by Google Generative API.

Open and run
1. Open Android Studio.
2. Choose "Open" and select this folder: `android-pic2text-app`.
3. Let Android Studio sync and install required SDK components.
4. Build and run on an emulator or device.

Command-line build (optional)
If you prefer command-line Gradle builds, Android Studio will create the proper Gradle wrapper. After that, you can run:
```bash
cd android-pic2text-app
./gradlew assembleDebug
./gradlew installDebug
```

Next steps (recommended)
- Update `NetworkClient.kt` with the correct Generative API URL, request format, and authentication method.
- Improve UI for batch processing, results listing, and output saving via Storage Access Framework.
- (Optional) Add a small backend to proxy requests if you want to avoid sending user keys directly to Google from the device.

If you want, I can continue and: scaffold CameraX capture, add Storage Access Framework save-to-folder, or produce a small example backend.
