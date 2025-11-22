#!/usr/bin/env python3
"""
OCR Image to Markdown using Google Gemini API
Equivalent to the n8n workflow for transcribing images to markdown text files.
"""

import argparse
import os
import sys
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
    
    # Match n8n workflow: original filename + .txt
    output_file = output_path / f"{input_file.name}.txt"
    
    print(f"Processing: {input_file.name}")
    
    markdown_text = transcribe_image(str(input_file), api_key, model)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown_text)
    
    print(f"Saved: {output_file}")
    return str(output_file)


def main():
    parser = argparse.ArgumentParser(
        description="OCR images to Markdown using Google Gemini API",
        epilog="Example: %(prog)s image.png doc.pdf --output ./transcriptions"
    )
    
    parser.add_argument("files", nargs="+", help="Image file(s) to process (.png, .jpg, .pdf)")
    parser.add_argument("-o", "--output", default="./files", help="Output directory (default: ./files)")
    parser.add_argument("-k", "--api-key", default=os.environ.get("GOOGLE_API_KEY"),
                        help="Google Gemini API key (or set GOOGLE_API_KEY env var)")
    parser.add_argument("-m", "--model", default="gemini-2.5-flash", help="Gemini model (default: gemini-2.5-flash)")
    
    args = parser.parse_args()
    
    if not args.api_key:
        print("Error: No API key provided.")
        print("Set GOOGLE_API_KEY environment variable or use --api-key flag")
        sys.exit(1)
    
    results, errors = [], []
    
    for file_path in args.files:
        try:
            output = process_file(file_path, args.output, args.api_key, args.model)
            results.append(output)
        except Exception as e:
            errors.append((file_path, str(e)))
            print(f"Error processing {file_path}: {e}")
    
    print(f"\nProcessed {len(results)} file(s) successfully")
    if errors:
        print(f"Failed: {len(errors)} file(s)")


if __name__ == "__main__":
    main()