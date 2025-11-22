# PythonProjects

A collection of small Python utilities and experiments focused on applying AI to practical tasks. This repository currently contains two desktop tools and a few helper scripts; more AI-driven projects may be added in the future.

This README is written to be generic and re-usable for future projects that involve generative AI or model-backed automation. It includes project summaries, run instructions, and suggested GitHub metadata to make publishing the repository easy.

---

**Current Projects**

- `BookMarketingGenerator/` — A GUI application that uses Google's Gemini models to generate book-marketing materials (blurbs, taglines, categories, ad copy, marketing strategies) from plain-text book files. Output is saved as Markdown reports.

- `Picture2text/` — A small GUI & script collection focused on extracting text from images/PDFs and converting it to Markdown (OCR-to-markdown). Integrates model-backed transcription where available.

Each project has its own README (inside its folder) with detailed setup and run steps. See `BookMarketingGenerator/README.md` and `Picture2text/README.md` (if present) for project-specific instructions.

---

**Repository Purpose (short)**

A workspace for lightweight, cross-platform Python tools that combine local GUI/CLI conveniences with cloud AI services for productivity tasks (marketing, OCR, content generation). Designed for indie authors, creators, and small teams who want practical AI helpers.

---

Quick links
- BookMarketingGenerator: `BookMarketingGenerator/book-marketing-generator.py`
- Picture2text: `Picture2text/ocr2md.py`

---

Getting started (non-technical friendly)

1. Install Python 3.8+ from https://python.org.
2. Open a Terminal (macOS) or PowerShell/Command Prompt (Windows).
3. Change to this repository folder, for example:

```bash
cd "~/GitHubProjects/PythonProjects"
```

4. For the first run, create a virtual environment (recommended):

macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

5. Install dependencies for the project you want to run. Each subfolder contains a README with suggested dependencies. As a common dependency, some tools use `google-generative-ai`:

```bash
pip install --upgrade pip
pip install google-generative-ai
```

6. Set your API key in the environment or paste into the app when prompted. Example (macOS/zsh):

```bash
export GOOGLE_API_KEY="YOUR_KEY"
```

Windows PowerShell:

```powershell
$env:GOOGLE_API_KEY = 'YOUR_KEY'
```

7. Run the script for the project you want. Example (macOS):

```bash
python3 BookMarketingGenerator/book-marketing-generator.py
```

---

Recommended repository metadata for GitHub (copy/paste into repo settings)

- Repository name: `PythonProjects` (or more specific like `ai-utilities`)  
- Short description (one line): "Small cross-platform Python utilities for practical AI tasks (book marketing, OCR, content generation)."  
- Topics / tags:
  - python
  - generative-ai
  - google-gemini
  - tkinter
  - automation
  - ocr
  - book-marketing

Suggested README overview blurb (for GitHub About or README top):

> A collection of lightweight Python tools that combine simple GUIs and cloud AI services to automate productivity tasks such as generating book marketing copy and converting images/PDFs to Markdown. Designed for quick setup and non-technical users.

Suggested first commit message:

```
chore: initial import — add BookMarketingGenerator and Picture2text projects
```

Suggested license: MIT (permissive and widely used). See `LICENSE` file included in this repo.

---

How to add a new AI project to this workspace (quick guide)

1. Create a folder under this repo with a short, descriptive name (e.g., `ai-title-generator`).
2. Add a short `README.md` in that folder with purpose, requirements, and run instructions.
3. Prefer a small CLI or GUI entrypoint `main.py` or similar and avoid heavy system-wide dependencies.
4. If using cloud APIs, document how to get API keys and add clear security notes in the project README.
5. Add tests or a `--dry-run` mode if possible so non-technical users can validate behavior without spending quota.

Template README snippet for new subprojects (paste into new folder):

```
# ProjectName

Short description — one sentence summary of what this does.

## Requirements
- Python 3.8+
- Dependencies: put in a list (e.g., google-generative-ai)

## Setup
1. Create & activate virtual environment
2. Install dependencies
3. Set `GOOGLE_API_KEY` environment variable or paste key into GUI

## Run
```bash
python main.py
```

## Notes
- Privacy note about sending text to external APIs
- Troubleshooting hints
```

---

Contributing & support

- Open an issue in this repository with errors, feature requests, or questions.
- Please include the exact command you ran, Python version, and any traceback for faster help.

---

If you want, I can:
- Add a short `README.md` file to `Picture2text/` if it is missing or expand the existing one.
- Add a `requirements.txt` per project listing dependencies.
- Initialize a `pyproject.toml` or `.gitignore` with useful defaults.

Tell me which of these you'd like me to add next and I'll create the files.