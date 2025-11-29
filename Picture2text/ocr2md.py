#!/usr/bin/env python3
"""
OCR Image to Markdown using Google Gemini API
With unified GUI form for batch processing.

Security Notes:
- API keys are masked in the UI but stored in memory while the app runs.
- Clearing the app from memory is recommended after use.
- Do NOT share your API key with others; it is your authentication credential.
- File paths are validated to prevent directory traversal attacks.
- Log output does not contain sensitive data (API keys, full file paths).
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
from pathlib import Path
import threading
from typing import Any
from datetime import datetime
import re
import logging
import webbrowser
import json

# Import google.generativeai in a way that avoids static attribute errors in editors
try:
    import google.generativeai as _genai  # type: ignore
except Exception:
    _genai = None  # type: ignore

# Expose a module-typed name so type-checkers won't complain about missing attributes
genai: Any = _genai

GEMINI_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
]

# Load pricing from external JSON file (allows easy updates without code changes)
def load_pricing_from_json() -> dict:
    """Load pricing data from pricing.json file. Falls back to hardcoded defaults if file not found."""
    pricing_file = Path(__file__).parent / "pricing.json"
    try:
        if pricing_file.exists():
            with open(pricing_file, "r") as f:
                data = json.load(f)
                # Convert nested model pricing to flat (model_name -> (input, output))
                return {
                    model: (info.get("input", 0.075), info.get("output", 0.30))
                    for model, info in data.get("models", {}).items()
                    if "input" in info and "output" in info
                }
    except Exception as e:
        logger.warning(f"Failed to load pricing.json: {e}. Using hardcoded defaults.")
    # Fallback hardcoded pricing (current as of Nov 2025)
    return {
        "gemini-2.5-pro": (0.075, 0.30),
        "gemini-2.5-flash": (0.075, 0.30),
        "gemini-2.5-flash-lite": (0.0375, 0.15),
        "gemini-2.0-flash": (0.075, 0.30),
        "gemini-2.0-flash-lite": (0.0375, 0.15),
        "gemini-1.5-pro": (0.075, 0.30),
        "gemini-1.5-flash": (0.075, 0.30),
    }

# Pricing per model (USD per 1M tokens) — loaded from external pricing.json
MODEL_PRICING = {}  # Will be initialized after logger setup

# Security: Configure logging to avoid exposing sensitive data
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Initialize pricing after logger is configured
MODEL_PRICING = load_pricing_from_json()

def is_valid_api_key(key: str) -> bool:
    """Validate API key format (basic check; Google keys are typically 39+ chars, alphanumeric + hyphens)."""
    if not key or len(key) < 20:
        return False
    # Google API keys contain alphanumeric, hyphens, underscores
    return bool(re.match(r'^[a-zA-Z0-9_-]{20,}$', key))

def validate_file_path(file_path: str, allowed_parent: Any = None) -> bool:
    """
    Validate file path to prevent directory traversal attacks.
    - Reject paths with '..'
    - Reject absolute paths (unless they match allowed_parent)
    - Reject symbolic links
    """
    try:
        path = Path(file_path)
        
        # Reject paths containing '..'
        if '..' in path.parts:
            return False
        
        # Check if file is a symbolic link (potential security issue)
        if path.is_symlink():
            logger.warning(f"Rejected symbolic link: {path.name}")
            return False
        
        # If allowed_parent is specified, ensure file is within it
        if allowed_parent:
            real_path = path.resolve()
            real_parent = allowed_parent.resolve()
            try:
                real_path.relative_to(real_parent)
            except ValueError:
                logger.warning(f"File outside allowed directory: {path.name}")
                return False
        
        return True
    except Exception as e:
        logger.error(f"Path validation error: {e}")
        return False

def sanitize_filename(filename: str) -> str:
    """Remove potentially dangerous characters from filename."""
    # Allow only alphanumeric, dots, hyphens, underscores
    safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    # Limit length to prevent filesystem issues
    return safe_name[:255]


def sanitize_prompt(prompt: str, max_len: int = 512) -> str:
    """Sanitize user-supplied prompt text before sending to the model.

    OWASP-inspired protections applied:
    - Remove non-printable/control characters
    - Trim and collapse excessive whitespace
    - Truncate to a reasonable maximum length
    - Remove obviously dangerous/injection-like fragments (simple blacklist)
    - Replace any long repeated characters to avoid abuse
    """
    if prompt is None:
        return ""
    # Normalize to string and strip
    p = str(prompt).strip()
    # Remove non-printable/control characters
    p = re.sub(r"[\x00-\x1f\x7f]+", " ", p)
    # Collapse multiple whitespace/newlines to single spaces
    p = re.sub(r"\s+", " ", p)
    # Remove simple suspicious sequences that could be used for injection
    blacklist = ["{{", "}}", "${", "<script", "</script>", "```"]
    for seq in blacklist:
        if seq in p:
            p = p.replace(seq, " ")
    # Replace extremely long repeated characters
    p = re.sub(r"(.)\1{100,}", r"\1", p)
    # Truncate to max length
    if len(p) > max_len:
        p = p[:max_len]
    # Final trim
    return p.strip()


def calculate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """Calculate cost in USD for a single API call based on token usage.
    
    Args:
        input_tokens: Number of input tokens (prompt + image)
        output_tokens: Number of output tokens (response)
        model: Model name
    
    Returns:
        Cost in USD (float)
    """
    if model not in MODEL_PRICING:
        logger.warning(f"Unknown model for pricing: {model}. Assuming gemini-2.5-flash pricing.")
        model = "gemini-2.5-flash"
    
    input_price_per_1m, output_price_per_1m = MODEL_PRICING[model]
    # Prices are per 1M tokens, so divide by 1,000,000
    input_cost = (input_tokens / 1_000_000) * input_price_per_1m
    output_cost = (output_tokens / 1_000_000) * output_price_per_1m
    return input_cost + output_cost

def validate_output_directory(output_dir: str) -> bool:
    """Validate output directory and ensure it can be safely created."""
    try:
        path = Path(output_dir)
        # Reject if path contains '..'
        if '..' in path.parts:
            return False
        # Try to create or validate it exists
        path.mkdir(parents=True, exist_ok=True)
        # Verify we can write to it
        test_file = path / ".ocr_test"
        test_file.touch()
        test_file.unlink()
        return True
    except Exception as e:
        logger.error(f"Output directory validation failed: {e}")
        return False

def get_mime_type(file_path: str, max_size_mb: int = 100) -> str:
    ext = Path(file_path).suffix.lower()
    mime_types = {
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".pdf": "application/pdf", ".webp": "image/webp", ".gif": "image/gif",
    }
    if ext not in mime_types:
        raise ValueError(f"Unsupported file type: {ext}")
    
    # Security: Validate file size (configurable, prevent DOS)
    file_size = Path(file_path).stat().st_size
    max_size = max_size_mb * 1024 * 1024
    if file_size > max_size:
        raise ValueError(f"File exceeds maximum size ({max_size_mb} MB): {Path(file_path).name}")
    if file_size == 0:
        raise ValueError(f"File is empty: {Path(file_path).name}")
    
    return mime_types[ext]


def transcribe_image(file_path: str, api_key: str, model: str = "gemini-2.5-flash", max_size_mb: int = 100, prompt: str | None = None) -> tuple[str, float]:
    """Transcribe image to markdown using Google Gemini.
    
    Returns:
        Tuple of (response_text, cost_in_usd)
    """
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
    mime_type = get_mime_type(file_path, max_size_mb)
    model_instance = genai.GenerativeModel(model)
    # Determine prompt text (sanitize defensively)
    prompt_text = sanitize_prompt(prompt) if prompt else "Transcribe this image to Markdown"
    if not prompt_text:
        prompt_text = "Transcribe this image to Markdown"
    # Retry logic with exponential backoff for transient errors
    max_retries = 3
    delay = 1.0
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        try:
            response = model_instance.generate_content([
                prompt_text,
                {"mime_type": mime_type, "data": file_data}
            ])
            # Extract token usage and calculate cost
            input_tokens = 0
            output_tokens = 0
            if hasattr(response, 'usage_metadata'):
                input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
                output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
            
            cost = calculate_cost(input_tokens, output_tokens, model)
            logger.info(f"Tokens: {input_tokens} input, {output_tokens} output. Cost: ${cost:.6f}")
            
            return response.text, cost
        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            # Retry on transient errors (rate limits, timeouts, temporary unavailability)
            is_retryable = any(x in err_str for x in ["429", "quota", "rate limit", "timeout", "temporarily", "unavailable"])
            
            if attempt < max_retries and is_retryable:
                logger.warning(f"Transient error on attempt {attempt}/{max_retries}: {e}. Retrying in {delay}s...")
                import time
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                raise
    
    # Should not reach here, but if we do, raise the last error
    raise last_error or RuntimeError("Max retries exceeded")


def process_file(input_path: str, output_dir: str, api_key: str, model: str = "gemini-2.5-flash", max_size_mb: int = 100, prompt: str | None = None) -> tuple[str, float]:
    """Process a single file and return output path and cost.
    
    Returns:
        Tuple of (output_file_path, cost_in_usd)
    """
    # Security: Validate input file path
    if not validate_file_path(input_path):
        raise ValueError(f"Invalid input file path: {Path(input_path).name}")
    
    input_file = Path(input_path)
    
    # Security: Validate output directory
    if not validate_output_directory(output_dir):
        raise ValueError(f"Invalid output directory: {output_dir}")
    
    output_path = Path(output_dir)
    
    # Security: Sanitize output filename
    safe_filename = sanitize_filename(input_file.name)
    output_file = output_path / f"{safe_filename}.txt"
    
    # Verify output file is still within output directory (prevent path traversal)
    if not validate_file_path(str(output_file), output_path):
        raise ValueError(f"Output file path validation failed")
    
    # 'prompt' may be provided by the GUI (caller should sanitize). Default preserved when prompt is None
    markdown_text, cost = transcribe_image(str(input_file), api_key, model, max_size_mb, prompt)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown_text)
    return str(output_file), cost


class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📷 OCR to Markdown")
        self.root.geometry("800x900")
        self.root.resizable(True, True)
        self.root.minsize(700, 850)
        
        self.selected_files = []
        # Default to Downloads directory (cross-platform)
        downloads_dir = str(Path.home() / "Downloads")
        self.output_folder = downloads_dir
        self.processing = False
        self.cancel_requested = False
        
        self.api_key_var = tk.StringVar(value=os.environ.get("GOOGLE_API_KEY", ""))
        self.selected_model = tk.StringVar(value=GEMINI_MODELS[1])
        self.max_file_size_mb = tk.IntVar(value=100)
        # Custom prompt the user can edit; default preserved
        self.custom_prompt_var = tk.StringVar(value="Transcribe this image to Markdown")
        
        # Security notice is shown inline under the API Key field (avoid popup on startup)

        self.create_widgets()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        # Top-level Help menu for discoverability
        menubar = tk.Menu(self.root)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Setup...", command=self.show_help)
        help_menu.add_separator()
        help_menu.add_command(label="About...", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menubar)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Title
        title = ttk.Label(main_frame, text="📷 OCR to Markdown", font=("Helvetica", 16, "bold"))
        title.grid(row=0, column=0, pady=(0, 15), sticky="w")
        
        # API Key Section
        api_frame = ttk.LabelFrame(main_frame, text="Google API Key", padding="10")
        api_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        api_frame.columnconfigure(0, weight=1)
        
        api_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, show="*", width=60)
        api_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        # (Environment setup instructions are available under Help → Setup)
        
        # Inline security notice (placed under the API key field so it's visible without a popup)
        notice_text = (
            "⚠️  SECURITY NOTICE — Your API key is stored in memory while the app runs."
            "Do NOT share your API key. Clear it after use or close the app when finished."
        )
        api_notice = ttk.Label(
            api_frame,
            text=notice_text,
            font=("Helvetica", 9),
            foreground="#8a2b2b",
            wraplength=760,
            justify="left"
        )
        api_notice.grid(row=1, column=0, sticky="w", pady=(6, 0))
        
        # Model Selection & File Size Limit (same row)
        settings_frame = ttk.Frame(main_frame)
        settings_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        settings_frame.columnconfigure(0, weight=1)
        settings_frame.columnconfigure(1, weight=1)
        
        model_frame = ttk.LabelFrame(settings_frame, text="Gemini Model", padding="10")
        model_frame.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        model_frame.columnconfigure(0, weight=1)
        
        model_combo = ttk.Combobox(model_frame, textvariable=self.selected_model, values=GEMINI_MODELS, state="readonly", width=30)
        model_combo.grid(row=0, column=0, sticky="ew")
        
        size_frame = ttk.LabelFrame(settings_frame, text="File Size Limit", padding="10")
        size_frame.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        # Make left column flexible so controls on the right can be pushed to the edge
        size_frame.columnconfigure(0, weight=1)
        size_frame.columnconfigure(1, weight=0)
        size_frame.columnconfigure(2, weight=0)
        
        size_label = ttk.Label(size_frame, text="Maximum (MB):")
        size_label.grid(row=0, column=0, sticky="w")
        
        size_spinbox = ttk.Spinbox(size_frame, from_=1, to=500, textvariable=self.max_file_size_mb, width=12)
        size_spinbox.grid(row=0, column=1, sticky="e", padx=(10, 0))

        # Small helper text on the same line as the spinbox (right-aligned)
        size_info = ttk.Label(size_frame, text="(1–500 MB)", font=("Helvetica", 9))
        size_info.grid(row=0, column=2, sticky="e", padx=(10, 0))

        # Prompt template (user-editable, sanitized before sending)
        prompt_frame = ttk.LabelFrame(settings_frame, text="Prompt Template", padding="10")
        prompt_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        prompt_frame.columnconfigure(0, weight=1)

        prompt_entry = ttk.Entry(prompt_frame, textvariable=self.custom_prompt_var, width=80)
        prompt_entry.grid(row=0, column=0, sticky="ew")

        def _reset_prompt():
            self.custom_prompt_var.set("Transcribe this image to Markdown")

        reset_btn = ttk.Button(prompt_frame, text="Reset", command=_reset_prompt)
        reset_btn.grid(row=0, column=1, padx=(6, 0))

        prompt_note = ttk.Label(prompt_frame, text="You may edit the prompt sent to the model. Input is sanitized for safety.", font=("Helvetica", 9))
        prompt_note.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))
        
        # Input Files Section
        input_frame = ttk.LabelFrame(main_frame, text="Input Files", padding="10")
        input_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        input_frame.columnconfigure(0, weight=1)
        
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=0, column=0, sticky="ew")
        
        select_btn = ttk.Button(btn_frame, text="Select Images...", command=self.select_files)
        select_btn.pack(side="left", padx=(0, 10))
        
        clear_btn = ttk.Button(btn_frame, text="Clear Selection", command=self.clear_files)
        clear_btn.pack(side="left")
        
        self.file_count_label = ttk.Label(btn_frame, text="No files selected")
        self.file_count_label.pack(side="left", padx=10)
        
        # Listbox to show selected files
        self.file_listbox = tk.Listbox(input_frame, height=5, selectmode=tk.EXTENDED)
        self.file_listbox.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        
        scrollbar = ttk.Scrollbar(input_frame, orient="vertical", command=self.file_listbox.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", pady=(10, 0))
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Output Folder Section
        output_frame = ttk.LabelFrame(main_frame, text="Output Directory", padding="10")
        output_frame.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        output_frame.columnconfigure(0, weight=1)
        
        output_entry = ttk.Entry(output_frame, width=60)
        output_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        output_entry.insert(0, self.output_folder)
        
        browse_btn = ttk.Button(output_frame, text="Browse...", command=self.browse_output)
        browse_btn.grid(row=0, column=1)
        
        self.output_label = output_entry
        
        # Progress Section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=5, column=0, sticky="ew", pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_label = ttk.Label(progress_frame, text="Ready")
        self.progress_label.grid(row=0, column=0, sticky="w")
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        
        self.progress_detail = ttk.Label(progress_frame, text="", font=("Helvetica", 9))
        self.progress_detail.grid(row=2, column=0, sticky="w", pady=(5, 0))
        
        # Log Output
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.grid(row=6, column=0, sticky="nsew", pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, state="disabled", wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        # Control Buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=7, column=0, sticky="ew", pady=(0, 5))
        
        self.start_btn = ttk.Button(control_frame, text="🚀 Start Processing", command=self.start_processing)
        self.start_btn.pack(side="left", padx=(0, 10))
        
        self.cancel_btn = ttk.Button(control_frame, text="Cancel", command=self.cancel_processing, state="disabled")
        self.cancel_btn.pack(side="left")
    
    def log(self, message):
        """Log message with automatic sanitization of sensitive data."""
        # Sanitize: remove API keys, tokens, and sensitive info
        sanitized = re.sub(r'[a-zA-Z0-9_-]{30,}', '[REDACTED]', message)
        
        self.log_text.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {sanitized}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")
    
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
            added = 0
            max_size_mb = self.max_file_size_mb.get()
            for f in files:
                # Security: Validate file path
                if not validate_file_path(f):
                    self.log(f"⚠️  Rejected file (invalid path): {Path(f).name}")
                    continue
                
                # Security: Validate file size
                try:
                    file_size = Path(f).stat().st_size
                    max_size = max_size_mb * 1024 * 1024
                    if file_size > max_size:
                        self.log(f"⚠️  Rejected file (exceeds {max_size_mb}MB): {Path(f).name}")
                        continue
                except Exception as e:
                    self.log(f"⚠️  Could not validate file: {Path(f).name}")
                    continue
                
                if f not in self.selected_files:
                    self.selected_files.append(f)
                    self.file_listbox.insert(tk.END, Path(f).name)
                    added += 1
            
            self.file_count_label.config(text=f"{len(self.selected_files)} file(s) selected")
            if added > 0:
                self.log(f"Added {added} file(s)")
    
    def clear_files(self):
        self.selected_files = []
        self.file_listbox.delete(0, tk.END)
        self.file_count_label.config(text="No files selected")
        self.log("Cleared file selection")
    
    def browse_output(self):
        # Open the directory picker at the currently shown output path (or fallback to default)
        current_dir = self.output_label.get().strip() or self.output_folder
        # Ensure initialdir exists; fallback to home if it doesn't
        try:
            initial = current_dir if Path(current_dir).exists() else self.output_folder
        except Exception:
            initial = self.output_folder

        directory = filedialog.askdirectory(title="Select Output Directory", initialdir=initial)
        if directory:
            self.output_folder = directory
            self.output_label.delete(0, tk.END)
            self.output_label.insert(0, directory)
            self.log(f"Output directory: {directory}")
    
    def get_api_key(self):
        key = self.api_key_var.get().strip()
        if not key:
            key = os.environ.get("GOOGLE_API_KEY", "")
        return key
    
    def validate_inputs(self):
        api_key = self.get_api_key()
        if not api_key:
            messagebox.showerror("Error", "Please enter your Google API Key or set the GOOGLE_API_KEY environment variable.")
            return False
        
        # Security: Validate API key format
        if not is_valid_api_key(api_key):
            messagebox.showerror("Error", "Invalid API Key format. Please check your key and try again.")
            return False
        
        if not self.selected_files:
            messagebox.showerror("Error", "Please select at least one image file.")
            return False
        
        # Security: Validate all selected files
        for file_path in self.selected_files:
            if not validate_file_path(file_path):
                messagebox.showerror("Error", f"Invalid file path detected. Please re-select files.")
                return False
        
        output_dir = self.output_label.get().strip()
        if not output_dir:
            messagebox.showerror("Error", "Please select an output directory.")
            return False
        
        # Security: Validate output directory
        if not validate_output_directory(output_dir):
            messagebox.showerror("Error", f"Cannot create or write to output directory. Please check permissions.")
            return False
        return True
    
    def start_processing(self):
        if not self.validate_inputs():
            return
        self.processing = True
        self.cancel_requested = False
        self.start_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress_bar["value"] = 0
        self.log(f"Starting processing with model: {self.selected_model.get()}")
        thread = threading.Thread(target=self.process_files, daemon=True)
        thread.start()
    
    def cancel_processing(self):
        self.cancel_requested = True
        self.log("Cancellation requested...")
    
    def update_progress(self, current, total, detail=""):
        progress = (current / total) * 100 if total > 0 else 0
        self.progress_bar["value"] = progress
        self.progress_label.configure(text=f"Processing: {current}/{total}")
        self.progress_detail.configure(text=detail)
    
    def process_files(self):
        try:
            if genai is None:
                self.log("ERROR: google.generativeai module is not installed.")
                self.root.after(0, lambda: messagebox.showerror("Error", "Required module 'google.generativeai' is not installed. Install with: pip install google-generative-ai"))
                return
            
            if hasattr(genai, "configure"):
                try:
                    genai.configure(api_key=self.get_api_key())
                except Exception:
                    pass
            
            total_files = len(self.selected_files)
            output_dir = self.output_label.get().strip()
            api_key = self.get_api_key()
            model = self.selected_model.get()
            max_size_mb = self.max_file_size_mb.get()
            # Sanitize prompt once and reuse for all files in this run
            prompt_text = sanitize_prompt(self.custom_prompt_var.get()) or None
            if prompt_text is None:
                # Ensure default if sanitization removed content
                prompt_text = "Transcribe this image to Markdown"
            
            results = []
            errors = []
            total_cost = 0.0
            
            for i, file_path in enumerate(self.selected_files, 1):
                if self.cancel_requested:
                    self.log("Processing cancelled by user.")
                    break
                
                filename = Path(file_path).name
                self.root.after(0, lambda c=i, t=total_files, d=filename: self.update_progress(c, t, d))
                self.log(f"Processing ({i}/{total_files}): {filename}")
                
                try:
                    output, cost = process_file(file_path, output_dir, api_key, model, max_size_mb, prompt_text)
                    results.append(output)
                    total_cost += cost
                    self.log(f"  ✓ Completed: {filename} — Cost: ${cost:.6f}")
                except Exception as e:
                    errors.append((filename, str(e)))
                    self.log(f"  ✗ Error: {filename} - {e}")
            
            if not self.cancel_requested:
                self.log("=" * 50)
                self.log(f"Processing complete: {len(results)}/{total_files} files processed")
                self.log(f"Total cost: ${total_cost:.6f}")
                if errors:
                    self.log(f"Failed: {len(errors)} file(s)")
                self.root.after(0, lambda: self.show_complete(len(results), total_files, errors, total_cost))
        
        except Exception as e:
            self.log(f"Fatal error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Processing failed: {e}"))
        finally:
            self.processing = False
            self.root.after(0, self.reset_ui)
    
    def reset_ui(self):
        self.start_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self.progress_label.configure(text="Ready")
        self.progress_detail.configure(text="")
    
    def clear_api_key(self):
        """Security: Clear API key from memory."""
        self.api_key_var.set("")

    def show_help(self):
        """Show a help dialog with installation and environment-variable instructions."""
        install_text = "pip install google-generative-ai"
        mac_text = 'export GOOGLE_API_KEY="paste-your-api-key-here"'
        win_text = '$env:GOOGLE_API_KEY = "paste-your-api-key-here"'

        combined = (
            "Required package:\n"
            "If you see: Required package 'google-generativeai' is not installed.\n\n"
            "Install with:\n"
            f"    {install_text}\n\n"
            "Set your environment API key using one of the following:\n\n"
            "macOS / Linux:\n"
            f"    {mac_text}\n\n"
            "Windows (PowerShell):\n"
            f"    {win_text}\n"
        )

        top = tk.Toplevel(self.root)
        top.title("Help & Setup")
        top.geometry("640x320")
        top.transient(self.root)
        top.grab_set()

        frame = ttk.Frame(top, padding="10")
        frame.pack(fill="both", expand=True)

        title = ttk.Label(frame, text="Help & Setup", font=("Helvetica", 12, "bold"))
        title.pack(anchor="w")

        txt = scrolledtext.ScrolledText(frame, height=12, wrap=tk.WORD, font=("Courier", 10))
        txt.insert("1.0", combined)
        # Keep the text widget read-only but allow selection/copy via the buttons
        txt.configure(state="disabled")
        txt.pack(fill="both", expand=True, pady=(6, 6))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x")

        def copy_install():
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(install_text)
                self.log("Copied install command to clipboard")
            except Exception:
                pass

        def copy_mac():
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(mac_text)
                self.log("Copied macOS/Linux env command to clipboard")
            except Exception:
                pass

        def copy_win():
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(win_text)
                self.log("Copied Windows (PowerShell) env command to clipboard")
            except Exception:
                pass

        def copy_all():
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(combined)
                self.log("Copied help content to clipboard")
            except Exception:
                pass

        copy_install_btn = ttk.Button(btn_frame, text="Copy Install", command=copy_install)
        copy_install_btn.pack(side="left", padx=(0, 6))

        copy_mac_btn = ttk.Button(btn_frame, text="Copy macOS", command=copy_mac)
        copy_mac_btn.pack(side="left", padx=(0, 6))

        copy_win_btn = ttk.Button(btn_frame, text="Copy Windows", command=copy_win)
        copy_win_btn.pack(side="left", padx=(0, 6))

        copy_all_btn = ttk.Button(btn_frame, text="Copy All", command=copy_all)
        copy_all_btn.pack(side="left", padx=(6, 6))

        close_btn = ttk.Button(btn_frame, text="Close", command=top.destroy)
        close_btn.pack(side="right")

    def show_about(self):
        """Show an About dialog with basic app info and a link to the repository."""
        repo_url = "https://github.com/dmburl/python-ai-projects"

        top = tk.Toplevel(self.root)
        top.title("About")
        top.geometry("480x220")
        top.transient(self.root)
        top.grab_set()

        frame = ttk.Frame(top, padding="10")
        frame.pack(fill="both", expand=True)

        title = ttk.Label(frame, text="OCR to Markdown", font=("Helvetica", 14, "bold"))
        title.pack(anchor="w")

        ver = ttk.Label(frame, text="Version: 0.1 — Developed by dmburl", font=("Helvetica", 9))
        ver.pack(anchor="w", pady=(4, 4))

        desc = ttk.Label(frame, text="A small GUI to transcribe images/PDFs to Markdown using Google Gemini.", wraplength=440)
        desc.pack(anchor="w", pady=(0, 8))

        link_label = ttk.Label(frame, text=repo_url, foreground="blue", cursor="hand2")
        link_label.pack(anchor="w")

        def open_repo(event=None):
            try:
                webbrowser.open(repo_url)
            except Exception:
                pass

        link_label.bind("<Button-1>", open_repo)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=(10, 0))

        def copy_repo():
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(repo_url)
                self.log("Copied repository URL to clipboard")
            except Exception:
                pass

        copy_btn = ttk.Button(btn_frame, text="Copy Repo URL", command=copy_repo)
        copy_btn.pack(side="left")

        open_btn = ttk.Button(btn_frame, text="Open in Browser", command=open_repo)
        open_btn.pack(side="left", padx=(6, 0))

        close_btn = ttk.Button(btn_frame, text="Close", command=top.destroy)
        close_btn.pack(side="right")
    
    def show_complete(self, success, total, errors, total_cost=0.0):
        msg = f"Successfully processed {success}/{total} files.\n\nOutput folder:\n{self.output_label.get()}"
        msg += f"\n\nTotal cost: ${total_cost:.6f}"
        if errors:
            msg += f"\n\nFailed ({len(errors)}):\n"
            msg += "\n".join([f"• {name}: {err}" for name, err in errors[:5]])
            if len(errors) > 5:
                msg += f"\n...and {len(errors) - 5} more"
        
        messagebox.showinfo("Processing Complete", msg)


def main():
    root = tk.Tk()
    
    # Set theme
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")
    
    app = OCRApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
