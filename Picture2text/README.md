# OCR to Markdown — Quick Start

This guide helps someone who has never used Python to run the `ocr2md.py` app. It covers installing Python, installing the script's dependency, how to get a Google API key, and how to run the app.

**What this app does:** Transcribes images (PNG/JPG/PDF) to Markdown using Google's Gemini (Generative AI) service and saves results as text files.

-**Files you should know:**
- `ocr2md.py` : The GUI app you will run.

**What is an API key:**
- Think of an API key like a password the app uses to talk to Google so Google will do the image transcription for you. Keep it secret like a password. Save it in a password manager so you have access to it when you need it. Change it like you would a password.

---

## Steps

**1) Install Python**

Pick the section that matches your computer.

- macOS:
  1. Visit https://www.python.org/downloads/ and click the latest Python 3 installer for macOS.
  2. Open the downloaded .pkg and follow the installer steps.
  3. After install, open `Terminal` (in Applications > Utilities) and run:
     ```bash
     python3 --version
     ```
     You should see a Python 3.x version.

- Windows:
  1. Visit https://www.python.org/downloads/ and download the latest Windows installer.
  2. During installation, check the box that says "Add Python to PATH" and then click Install.
  3. Open Command Prompt and run:
     ```bash
     python --version
     ```
     You should see a Python 3.x version.

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

Open a Terminal (macOS/Linux) or Command Prompt / PowerShell (Windows). 
In the folder that contains the script `ocr2md.py`, 
run these commands:

macOS / Linux:
```bash
python3 -m pip install --upgrade pip
pip3 install google-generativeai
```

Windows (Command Prompt / PowerShell):
```powershell
python -m pip install --upgrade pip
pip install google-generativeai
```

If the commands above fail, try `python` instead of `python3`, or run the commands as an Administrator on Windows.

---

**3) Get a Google API key (step-by-step for beginners)**

Below are step-by-step instructions with extra detail and troubleshooting tips. If you are new to Google Cloud, follow these steps slowly and keep this tab open while you work in the Cloud Console.

1) Sign in / create a Google account
- Open a web browser and go to https://console.cloud.google.com/
- If you already have a Google account, click `Sign in`. If not, click `Create account` and follow the prompts to make a new Google account.

2) Create a new Google Cloud Project
- In the Cloud Console, find the **Select a project** dropdown near the top of the page and choose **New Project**.
- Give the project a simple name, e.g. `ocr2md-project`, and click **Create**. The console may take a few seconds to initialize the project and switch to the new project context.

3) Enable billing for the project (required)
- Google requires billing enabled to use Generative AI services. In the Cloud Console, open the **Billing** section from the left-hand menu and attach or create a billing account.
- If you don't have a billing account you will be prompted to create one; Google commonly offers a free trial credit for new accounts.
- Tip: After attaching billing, immediately create a budget and alert in **Billing → Budgets & alerts** to avoid unexpected charges.

4) Enable the Generative AI / Gemini API for the project
- Navigate to **APIs & Services → Library** from the left-hand menu.
- Use the search box to type `Generative` or `Generative AI` (results may show "Gemini API", "Generative AI", "Generative Language", or similar). Click the matching API and then click **Enable**.
- Wait a few seconds after enabling — the API needs to be activated for your project.

5) Create an API key
- Go to **APIs & Services → Credentials**.
- Click **Create Credentials** and select **API key**.
- A dialog will display your new API key. Click the small copy icon to copy it to your clipboard now — **this is the only time the full key is shown.**

6) (Optional but recommended) Restrict or rotate the key
- After creating the key you can click the key name and use **Key restrictions** to reduce risk:
  - **Application restrictions**
    - For server-hosted usage, restrict by IP address.
    - For browser usage, restrict by HTTP referrers.
    - For desktop apps (like this GUI) strict restrictions may not be practical; instead rotate the key periodically and keep it private.
  - **API Restrictions**
    - Select **Restrict key**
    - Select **API Keys** and **Generative Language API**
- If the key is ever exposed, delete/regenerate it immediately in **APIs & Services → Credentials**.

7) Paste or store your API key safely
- Store your API key safely in a password manager. This will give you future access to it.
- Beginner: launch the GUI and paste the API key into the `Google Gemini API Key` field.
- Advanced: set an environment variable named `GOOGLE_API_KEY` so the app picks it up automatically.

  macOS / Linux (temporary for current terminal session):
  ```bash
  export GOOGLE_API_KEY="paste-your-api-key-here"
  python3 ocr2md.py
  ```

  macOS / Linux (persist for your user): add to `~/.bash_profile` or `~/.zshrc`:
  ```bash
  echo 'export GOOGLE_API_KEY="paste-your-api-key-here"' >> ~/.zshrc
  source ~/.zshrc
  ```

  Windows PowerShell (temporary for current session):
  ```powershell
  $env:GOOGLE_API_KEY = "paste-your-api-key-here"
  python ocr2md.py
  ```

  Windows (persist across sessions)(**Not Recommneded**):
  - Only do this on your personal system that you have access to. This puts your API Key into a location any application can see it.
  - Open **Start → Settings → System → About → Advanced system settings → Environment Variables** and add a new user variable named `GOOGLE_API_KEY` with the key value.

8) Security reminders and what to do if the key is exposed
- Treat the API key like a password. If someone else gets your key they could use your Google project and incur charges.
- If you believe the key has been exposed: Got to: https://console.cloud.google.com/ then **APIs & Services → Credentials**, find the key, and **Delete** or **Regenerate** it immediately. Then update your app or environment with the new key.

9) Troubleshooting & where to check usage
- If you cannot enable the API: confirm billing is enabled and verify the project selector shows the project you created.
- If the key does not work: ensure you copied the whole key (no extra spaces), that the Generative AI API is enabled on the same project, and billing is active.
- To view logs, errors, and quota usage: open **APIs & Services → Dashboard**, select the Generative AI API, and inspect the metrics and logs.

The API key is what the app pastes into a secure slot so Google knows which project is requesting the transcription.

---

**4) Run the app**

**Option A** — Paste the key into the app (recommended):
1. Start the app:
  - macOS / Linux: `python3 ocr2md.py`
  - Windows: `python ocr2md.py`
2. When the GUI opens, paste the API key into the "Google Gemini API Key" box. You do not need to set environment variables.
3. Click "Select Files" to pick images or PDFs. Click "Select Folder" to pick where to save results.
4. Click "Start Processing".

**Option B** — Set an environment variable (optional):
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

**5) Troubleshooting**
- If you see an error about `google-generativeai` not installed: run `pip install google-generativeai` and then try again.
- If the GUI does not open and you see errors about `tkinter`:
  - **On macOS:** make sure you installed Python from python.org (the installer includes tkinter support). If you used Homebrew Python and tkinter is missing, install the Tcl/Tk frameworks or use python.org installer.
  - **On Linux:** install `python3-tk` (example `sudo apt install python3-tk`).
- If Google refuses the API key or you get authentication errors: double-check you copied the key correctly, that the correct project is selected in Google Cloud, and that billing is enabled.

---

**6) Safety and cost notes**
- Using Google Generative APIs may incur charges — check your Google Cloud Console Billing page to monitor usage and set spending alerts.