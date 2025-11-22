# OCR to Markdown — Quick Start (Non-technical friendly)

This guide helps someone who has never used Python to run the `ocr-script-single-form1.py` app. It covers installing Python, installing the script's dependency, how to get a Google API key (very simple explanation), and how to run the app.

**What this app does:** Transcribes images (PNG/JPG/PDF) to Markdown using Google's Gemini (Generative AI) service and saves results as text files.

-**Files you should know:**
- `ocr2md.py` : The GUI app you will run.
- `requirements.txt` : The Python dependency file (used for installing required packages).

**Short non-technical explanation of an API key:**
- Think of an API key like a password the app uses to talk to Google so Google will do the image transcription for you. Keep it secret like a password.

---

**1) Install Python**

Pick the section that matches your computer.

- macOS (recommended):
  1. Visit https://www.python.org/downloads/ and click the latest Python 3 installer for macOS.
  2. Open the downloaded .pkg and follow the installer steps.
  3. After install, open `Terminal` (in Applications > Utilities) and run:
     ```bash
     python3 --version
     ```
     You should see a Python 3.x version.

- Windows:
  1. Visit https://www.python.org/downloads/windows and download the latest Windows installer.
  2. During installation, check the box that says "Add Python to PATH" and then click Install.
  3. Open Command Prompt and run:
     ```powershell
     python --version
     ```

- Linux (Ubuntu/Debian example):
  1. Open Terminal and run:
     ```bash
     sudo apt update
     sudo apt install python3 python3-venv python3-pip python3-tk -y
     python3 --version
     ```

Notes:
- On macOS, using the installer from python.org is simpler for non-technical users because it includes things needed for the GUI (`tkinter`). If Tkinter GUI fails, try reinstalling from python.org instead of the system Python.

---

**2) Install the app's Python dependency**

Open a Terminal (macOS/Linux) or Command Prompt / PowerShell (Windows). In the folder that contains the script and `requirements.txt`, run these commands:

macOS / Linux:
```bash
cd "path/to/Python OCR"
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt
```

Windows (Command Prompt / PowerShell):
```powershell
cd "C:\path\to\Python OCR"
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If the commands above fail, try `python` instead of `python3`, or run the commands as an Administrator on Windows.

---

**3) Get a Google API key (step-by-step, non-technical)**

1. Create or sign in to a Google account at https://accounts.google.com/
2. Open the Google Cloud Console: https://console.cloud.google.com/
3. Create a new **Project** (there's usually a "Select a project" dropdown near the top — choose "New Project").
4. Enable billing for the project. (Google requires billing to use their generative APIs; you may get a free trial credit when first enabling billing.)
5. Enable the Generative AI / Gemini API for the project:
   - In Cloud Console, go to **APIs & Services → Library**.
   - Search for "Generative" or "Generative AI" or "Generative Language" and click the result, then click **Enable**.
6. Create an API key:
   - Go to **APIs & Services → Credentials**.
   - Click **Create Credentials → API key**.
   - A new key appears: click the copy icon to copy it to your clipboard.
7. IMPORTANT: Treat this key like a password — don't share it.

Simple explanation: the API key is what the app pastes into a secure slot so Google knows who is asking to transcribe the images.

---

**4) Run the app (quickest for non-technical users)**

Option A — Paste the key into the app (recommended):
1. Start the app:
  - macOS / Linux: `python3 ocr2md.py`
  - Windows: `python ocr2md.py`
2. When the GUI opens, paste the API key into the "Google Gemini API Key" box. You do not need to set environment variables.
3. Click "Select Files" to pick images or PDFs. Click "Select Folder" to pick where to save results.
4. Click "Start Processing".

Option B — Set an environment variable (optional):
- macOS / Linux:
  ```bash
  export GOOGLE_API_KEY="paste-your-api-key-here"
  python3 ocr2md.py
  ```
- Windows (PowerShell temporary for that session):
  ```powershell
  $env:GOOGLE_API_KEY = "paste-your-api-key-here"
  python ocr2md.py
  ```

---

-**5) Troubleshooting**
- If you see an error about `google-generativeai` not installed: run `pip install -r requirements.txt` and then try again.
- If the GUI does not open and you see errors about `tkinter`:
  - On macOS: make sure you installed Python from python.org (the installer includes tkinter support). If you used Homebrew Python and tkinter is missing, install the Tcl/Tk frameworks or use python.org installer.
  - On Linux: install `python3-tk` (example `sudo apt install python3-tk`).
- If Google refuses the API key or you get authentication errors: double-check you copied the key correctly, that the correct project is selected in Google Cloud, and that billing is enabled.

---

**6) Safety and cost notes**
- Using Google Generative APIs may incur charges — check your Google Cloud Console Billing page to monitor usage and set spending alerts.

---

If you'd like, I can also:
- Create simple `run_mac.sh` and `run_windows.bat` wrapper files so users can double-click to run the app.
- Add screenshots to this README to make the steps even easier.

If you want me to add a double-click runnable wrapper, tell me which OS(s) you'd like me to support and I'll add them.

---

**Double-click wrappers (added)**

- `run_mac.sh` — A small launcher script for macOS. To run by double-clicking:
  - Make it executable (one-time):
    ```bash
    chmod +x run_mac.sh
    ```
  - If double-clicking opens the file in an editor instead of running it, rename it to `run_mac.command` and then double-click — or open Terminal and run `./run_mac.sh`.
  - The script runs the system `python3` interpreter to start `ocr2md.py`.

- `run_windows.bat` — A Windows batch file you can double-click. It runs the system `python` to start `ocr2md.py`. The window will remain open after completion so you can read messages.

Note: The project no longer requires creating or activating a virtual environment. The launchers call the system Python directly; ensure Python is installed and available on `PATH`.
