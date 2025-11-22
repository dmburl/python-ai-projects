## Complete Setup Guide for Windows

### Step 1: Download Python

1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Click the big yellow "Download Python 3.x.x" button
3. Run the downloaded installer (e.g., `python-3.12.x-amd64.exe`)

**IMPORTANT during installation:**
- ✅ Check the box that says **"Add python.exe to PATH"** at the bottom of the first screen
- Click "Install Now"

### Step 2: Verify Python Installed

1. Press `Windows + R`, type `cmd`, press Enter to open Command Prompt
2. Type:
   ```cmd
   python --version
   ```
   You should see something like `Python 3.12.4`

If you get "python is not recognized", restart your computer and try again (PATH needs to refresh).

### Step 3: Install the Required Library

In the same Command Prompt window, run:
```cmd
pip install google-generativeai
```

Wait for it to finish downloading and installing.

### Step 4: Get a Google Gemini API Key

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (it looks like `AIzaSy...`)

### Step 5: Save the Script

1. Open Notepad
2. Copy and paste the entire Python script
3. Click File → Save As
4. Change "Save as type" to **"All Files (*.*)"**
5. Name it `ocr_to_markdown.py`
6. Save it somewhere easy to find (e.g., Desktop or Documents)

### Step 6: Run the Script

**Option A: Command Prompt**
```cmd
cd Desktop
python ocr_to_markdown.py
```

**Option B: Double-click**
- Right-click the `.py` file → "Open with" → "Python"

---

## Summary of Commands

```cmd
# After installing Python from python.org:
python --version
pip install google-generativeai
python ocr_to_markdown.py
```

---

## Optional: Set API Key Permanently

If you don't want to paste the API key every time:

1. Press `Windows + R`, type `sysdm.cpl`, press Enter
2. Go to **Advanced** tab → **Environment Variables**
3. Under "User variables", click **New**
4. Variable name: `GOOGLE_API_KEY`
5. Variable value: `AIzaSy...` (your actual key)
6. Click OK, OK, OK

Now the script will automatically use that key when the field is left blank.