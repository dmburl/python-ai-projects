#!/usr/bin/env python3
"""
OCR Image to Markdown using Google Gemini API
With GUI file selector for batch processing.
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from pathlib import Path

try:
    import google.generativeai as genai
except ImportError:
    print("Error: google-generativeai package not installed.")
    print("Install it with: pip install google-generativeai")
    sys.exit(1)


def get_mime_type(file_path: str) -> str:
    """Determine MIME type based on file extension."""
    ext = Path(file_path).suffix.lower()
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".pdf": "application/pdf",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    if ext not in mime_types:
        raise ValueError(f"Unsupported file type: {ext}")
    return mime_types[ext]


def transcribe_image(file_path: str, api_key: str, model: str = "gemini-2.5-flash") -> str:
    """Send image to Gemini API and get markdown transcription."""
    genai.configure(api_key=api_key)
    
    with open(file_path, "rb") as f:
        file_data = f.read()
    
    mime_type = get_mime_type(file_path)
    model_instance = genai.GenerativeModel(model)
    
    response = model_instance.generate_content([
        "Transcribe this image to Markdown",
        {"mime_type": mime_type, "data": file_data}
    ])
    
    return response.text


def process_file(input_path: str, output_dir: str, api_key: str, model: str) -> str:
    """Process a single file and save the transcription."""
    input_file = Path(input_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    output_file = output_path / f"{input_file.name}.txt"
    
    markdown_text = transcribe_image(str(input_file), api_key, model)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown_text)
    
    return str(output_file)


def select_files() -> list:
    """Open file dialog to select multiple files."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    files = filedialog.askopenfilenames(
        title="Select Images to OCR",
        filetypes=[
            ("Supported files", "*.png *.jpg *.jpeg *.pdf *.webp *.gif"),
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("PDF files", "*.pdf"),
            ("All files", "*.*")
        ]
    )
    
    root.destroy()
    return list(files)


def select_output_folder() -> str:
    """Open folder dialog to select output directory."""
    root = tk.Tk()
    root.withdraw()
    
    folder = filedialog.askdirectory(
        title="Select Output Folder for Transcriptions"
    )
    
    root.destroy()
    return folder if folder else "./files"


def get_api_key() -> str:
    """Get API key from environment or prompt user."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    
    if not api_key:
        root = tk.Tk()
        root.withdraw()
        
        api_key = simpledialog.askstring(
            "API Key Required",
            "Enter your Google Gemini API Key:",
            show='*'  # Hide input like a password
        )
        
        root.destroy()
    
    return api_key


def show_progress(current: int, total: int, filename: str):
    """Print progress to console."""
    print(f"[{current}/{total}] Processing: {filename}")


def main():
    print("=== OCR to Markdown Tool ===\n")
    
    # Get API key
    api_key = get_api_key()
    if not api_key:
        print("Error: No API key provided. Exiting.")
        sys.exit(1)
    
    # Select files
    print("Opening file selector...")
    files = select_files()
    
    if not files:
        print("No files selected. Exiting.")
        sys.exit(0)
    
    print(f"\nSelected {len(files)} file(s)")
    
    # Select output folder
    print("Opening output folder selector...")
    output_dir = select_output_folder()
    print(f"Output folder: {output_dir}\n")
    
    # Process all files
    results = []
    errors = []
    total = len(files)
    
    for i, file_path in enumerate(files, 1):
        filename = Path(file_path).name
        show_progress(i, total, filename)
        
        try:
            output = process_file(file_path, output_dir, api_key, "gemini-2.5-flash")
            results.append(output)
            print(f"    ✓ Saved: {Path(output).name}")
        except Exception as e:
            errors.append((filename, str(e)))
            print(f"    ✗ Error: {e}")
    
    # Summary
    print(f"\n{'='*40}")
    print(f"COMPLETE: {len(results)}/{total} files processed successfully")
    
    if errors:
        print(f"\nFailed files ({len(errors)}):")
        for filename, err in errors:
            print(f"  - {filename}: {err}")
    
    # Show completion dialog
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(
        "OCR Complete",
        f"Processed {len(results)}/{total} files.\n\nOutput folder:\n{output_dir}"
    )
    root.destroy()


if __name__ == "__main__":
    main()
