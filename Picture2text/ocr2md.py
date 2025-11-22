#!/usr/bin/env python3
"""
OCR Image to Markdown using Google Gemini API
With unified GUI form for batch processing.
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading
from typing import Any

# Import google.generativeai in a way that avoids static attribute errors in editors
try:
    import google.generativeai as _genai  # type: ignore
except Exception:
    _genai = None  # type: ignore

# Expose a module-typed name so type-checkers won't complain about missing attributes
genai: Any = _genai


def get_mime_type(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    mime_types = {
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".pdf": "application/pdf", ".webp": "image/webp", ".gif": "image/gif",
    }
    if ext not in mime_types:
        raise ValueError(f"Unsupported file type: {ext}")
    return mime_types[ext]


def transcribe_image(file_path: str, api_key: str, model: str = "gemini-2.5-flash") -> str:
    if genai is None:
        raise RuntimeError("Required package 'google-generativeai' is not installed. Install with: pip install google-generative-ai")

    # configure if supported
    if hasattr(genai, "configure"):
        try:
            genai.configure(api_key=api_key)
        except Exception:
            # ignore configure failures (some versions use env vars)
            pass
    with open(file_path, "rb") as f:
        file_data = f.read()
    mime_type = get_mime_type(file_path)
    model_instance = genai.GenerativeModel(model)
    response = model_instance.generate_content([
        "Transcribe this image to Markdown",
        {"mime_type": mime_type, "data": file_data}
    ])
    return response.text


def process_file(input_path: str, output_dir: str, api_key: str) -> str:
    input_file = Path(input_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / f"{input_file.name}.txt"
    markdown_text = transcribe_image(str(input_file), api_key)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown_text)
    return str(output_file)


class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OCR to Markdown")
        self.root.geometry("600x700")
        self.root.resizable(True, True)
        self.root.minsize(500, 700)
        
        self.selected_files = []
        self.output_folder = "./files"
        self.processing = False
        
        self.create_widgets()
    
    def create_widgets(self):
        # Instructions
        instructions = ttk.LabelFrame(self.root, text="Instructions", padding=10)
        instructions.pack(fill="x", padx=15, pady=(15, 10))
        
        inst_text = (
            "1. Click 'Select Files' to choose images/PDFs to transcribe (multi-select supported)\n"
            "2. Click 'Select Folder' to choose where to save the output .txt files\n"
            "3. Enter your Google Gemini API key (or leave blank to use GOOGLE_API_KEY env variable)\n"
            "4. Click 'Start Processing' to begin OCR transcription"
        )
        ttk.Label(instructions, text=inst_text, justify="left").pack(anchor="w")
        
        # Input Files Section
        input_frame = ttk.LabelFrame(self.root, text="Input Files", padding=10)
        input_frame.pack(fill="x", padx=15, pady=5)
        
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill="x")
        
        ttk.Button(btn_frame, text="Select Files", command=self.select_files).pack(side="left")
        self.file_count_label = ttk.Label(btn_frame, text="No files selected")
        self.file_count_label.pack(side="left", padx=10)
        
        # Listbox to show selected files
        list_frame = ttk.Frame(input_frame)
        list_frame.pack(fill="x", pady=(10, 0))
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.file_listbox = tk.Listbox(list_frame, height=5, yscrollcommand=scrollbar.set)
        self.file_listbox.pack(fill="x", side="left", expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
        # Output Folder Section
        output_frame = ttk.LabelFrame(self.root, text="Output Folder", padding=10)
        output_frame.pack(fill="x", padx=15, pady=5)
        
        out_btn_frame = ttk.Frame(output_frame)
        out_btn_frame.pack(fill="x")
        
        ttk.Button(out_btn_frame, text="Select Folder", command=self.select_output).pack(side="left")
        self.output_label = ttk.Label(out_btn_frame, text=self.output_folder)
        self.output_label.pack(side="left", padx=10)
        
        # API Key Section
        api_frame = ttk.LabelFrame(self.root, text="Google Gemini API Key", padding=10)
        api_frame.pack(fill="x", padx=15, pady=5)
        
        ttk.Label(api_frame, text="Leave blank to use GOOGLE_API_KEY environment variable").pack(anchor="w")
        self.api_entry = ttk.Entry(api_frame, width=60, show="*")
        self.api_entry.pack(fill="x", pady=(5, 0))
        
        # Pre-fill if env var exists
        env_key = os.environ.get("GOOGLE_API_KEY", "")
        if env_key:
            self.api_entry.insert(0, env_key)
        
        # Progress Section
        progress_frame = ttk.LabelFrame(self.root, text="Progress", padding=10)
        progress_frame.pack(fill="x", padx=15, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x")
        
        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.pack(anchor="w", pady=(5, 0))
        
        # Start Button
        self.start_btn = ttk.Button(self.root, text="Start Processing", command=self.start_processing)
        self.start_btn.pack(pady=20, ipadx=20, ipady=10)
    
    def select_files(self):
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
        if files:
            self.selected_files = list(files)
            self.file_count_label.config(text=f"{len(self.selected_files)} file(s) selected")
            self.file_listbox.delete(0, tk.END)
            for f in self.selected_files:
                self.file_listbox.insert(tk.END, Path(f).name)
    
    def select_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder = folder
            self.output_label.config(text=folder)
    
    def get_api_key(self):
        key = self.api_entry.get().strip()
        if not key:
            key = os.environ.get("GOOGLE_API_KEY", "")
        return key
    
    def start_processing(self):
        if self.processing:
            return
        
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select files to process.")
            return
        
        api_key = self.get_api_key()
        if not api_key:
            messagebox.showerror("No API Key", "Please enter an API key or set GOOGLE_API_KEY environment variable.")
            return
        
        self.processing = True
        self.start_btn.config(state="disabled")
        
        # Run in separate thread to keep UI responsive
        thread = threading.Thread(target=self.process_files, args=(api_key,))
        thread.start()
    
    def process_files(self, api_key):
        total = len(self.selected_files)
        results, errors = [], []
        
        for i, file_path in enumerate(self.selected_files, 1):
            filename = Path(file_path).name
            self.update_status(f"Processing ({i}/{total}): {filename}")
            self.progress_var.set((i - 1) / total * 100)
            
            try:
                output = process_file(file_path, self.output_folder, api_key)
                results.append(output)
            except Exception as e:
                errors.append((filename, str(e)))
        
        self.progress_var.set(100)
        self.update_status(f"Complete: {len(results)}/{total} files processed")
        
        # Show completion message
        self.root.after(0, lambda: self.show_complete(len(results), total, errors))
    
    def update_status(self, text):
        self.root.after(0, lambda: self.status_label.config(text=text))
    
    def show_complete(self, success, total, errors):
        self.processing = False
        self.start_btn.config(state="normal")
        
        msg = f"Successfully processed {success}/{total} files.\n\nOutput folder:\n{self.output_folder}"
        if errors:
            msg += f"\n\nFailed ({len(errors)}):\n"
            msg += "\n".join([f"• {name}: {err}" for name, err in errors[:5]])
            if len(errors) > 5:
                msg += f"\n...and {len(errors) - 5} more"
        
        messagebox.showinfo("Processing Complete", msg)


def main():
    root = tk.Tk()
    app = OCRApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
