# Gemini Book Marketing Generator

A small GUI app that uses Google's Gemini API (via the `google-generative-ai` Python package) to generate book-marketing content from a selected book text file. This README explains how a non-technical user can set up and run the script on macOS or Windows.

**File:** `book-marketing-generator.py`

---

## What this app does
- Lets you select one or more local book files.
- Sends prompts (marketing tasks) to a Gemini model and saves a Markdown report for each file.
- Provides a basic progress view and a log window.

> Note: The script expects readable text files (plain `.txt`) as input. PDF or other binary file support may not work reliably unless the PDF contains extractable text.

---

## Requirements
- A computer running macOS or Windows.
- Python 3.8 or newer installed.
- A Google Gemini API key (Google Cloud / Gemini access) with sufficient quota.
- Internet connection to call the Gemini API.

External Python dependency (installed via `pip`):
- `google-generative-ai`

The GUI uses `tkinter` which is bundled with most Python installations. If `tkinter` is missing, see the Troubleshooting section below.

---

## Before you start — get an API key
1. Create or sign in to a Google Cloud account and enable the Generative AI / Gemini APIs according to Google's documentation.
2. Create an API key or service account with a key you can use for the script.
3. Copy the API key string — you will enter it into the app or set it as an environment variable.

If you are unsure how to get an API key, ask whoever manages your Google Cloud account or follow Google's official guide.

---

## Installation & Run (macOS / Linux - zsh)
1. Open Terminal.
2. (Recommended) Create and activate a Python virtual environment:

```bash
python3 -m venv ~/gm_venv
source ~/gm_venv/bin/activate
```

3. Install the required package:

```bash
pip install --upgrade pip
pip install google-generative-ai
```

4. (Optional) Set your API key as an environment variable so you don't have to type it into the app each time:

```bash
export GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_HERE"
```

5. Run the app (replace the path if your repository is elsewhere):

```bash
python3 "/<path>/book-marketing-generator.py"
```

---

## Installation & Run (Windows PowerShell)
1. Open PowerShell (press Start, type PowerShell, run it).
2. (Recommended) Create and activate a virtual environment:

```powershell
python -m venv C:\gm_venv
C:\gm_venv\Scripts\Activate.ps1
```

3. Install the required package:

```powershell
python -m pip install --upgrade pip
python -m pip install google-generative-ai
```

4. (Optional) Set the API key for this PowerShell session:

```powershell
$env:GOOGLE_API_KEY = 'YOUR_GOOGLE_API_KEY_HERE'
```

5. Run the app (adjust the path if different):

```powershell
python "C:\<path>\book-marketing-generator.py"
```

(If you prefer Command Prompt use `set GOOGLE_API_KEY=...` and run with `python`.)

---

## Using the app (GUI)
1. When the app opens, you will see fields for:
   - Google API Key (you can paste it here if you didn't set the environment variable)
   - Model selection (choose a Gemini model from the dropdown)
   - Buttons to select book files and choose an output folder
2. Click `Select Book Files...` and pick one or more plain text files (`.txt`) containing your book or book excerpt.
3. Click `Browse...` next to Output Directory and choose a folder where the Markdown reports should be saved.
4. Enter your API key if needed, or confirm the `GOOGLE_API_KEY` environment variable is set.
5. Click `🚀 Start Processing` to begin. Progress will be shown in the window and reports will be saved as `YourBookName_Marketing_Report.md`.

When processing completes a dialog will confirm the results.

---

## Troubleshooting
- "Module not found" or import errors for `google.generativeai`:
  - Ensure you installed the package in the same Python you run the script with: `python -m pip install google-generative-ai`.
  - If using a virtual environment, make sure it is activated before running the script.

- `tkinter` missing on Windows:
  - Install the standard Python distribution from python.org which includes `tkinter`.

- 429 / quota errors from the Gemini API:
  - These mean your API quota is exhausted or you're hitting rate limits. Wait and try again, or request higher quota from your Google Cloud admin.
  - The app has retry logic for transient errors, but persistent 429s will appear as errors in the generated report.

- Input files are unreadable / empty output:
  - The generator expects plain text files. If you try to feed binary formats (some PDFs, eBooks), extraction may fail. Convert PDFs to plain text first or extract text with a PDF reader.

- Reports not appearing in the folder:
  - Confirm you selected the correct Output Directory in the app before starting.
  - Check the app's log window for error messages.

---

## Security notes
- The app will send text of your selected files to Google's Gemini API — do not send private/confidential text unless you have permission and the appropriate data protections in place.
- Keep your API key secret. Do not share screenshots that show the key.

---

## Optional tweaks / advanced
- If you want the app to run without a GUI, you can extract the processing logic into a small CLI wrapper — ask for help if you want that.
- If you mostly have PDFs, consider adding a PDF-to-text extractor (e.g., `pdfplumber` or `PyMuPDF`) before sending content to Gemini.

---

## Where to get help
- If you hit an error you can't resolve, copy the exact error text and share it with the maintainer or include it in a support request — that will speed troubleshooting.

---

Enjoy using the Gemini Book Marketing Generator! If you'd like, I can:
- Add a simple CLI mode to process files without opening the GUI.
- Add PDF text extraction so PDFs are handled automatically.
- Add an offline/mock mode so you can test the GUI without an API key.

If you want any of those, tell me which and I'll add it.
