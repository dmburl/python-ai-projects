"""
Gemini Book Marketing Generator
A Python GUI application that generates comprehensive book marketing content using Google's Gemini API.
"""

import os
import sys
import threading
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Any
import time

try:
    import google.generativeai as _genai  # type: ignore
except Exception:
    _genai = None  # type: ignore

# Expose `genai` as `Any` so static type checkers don't error on attribute access.
genai: Any = _genai


class ModelCallError(Exception):
    """Raised when the model call fails in a way that may be retried or reported."""
    pass

# Marketing prompts from the n8n workflow
MARKETING_PROMPTS = [
    "Based on the book's [Genre, Subgenres, and general content], define the following: The Primary Genre and 3 Subgenres. A compelling Core Promise (a single sentence emotional theme, e.g., 'A story of finding hope after disaster').",
    "Create a detailed Target Audience profile. Include demographics (age, gender), reading preferences (e.g., high-angst, low-spice, literary), and 3-5 comparable authors or media they already enjoy.",
    "Generate a list of 10-15 key tropes, story conventions, and recognizable plot elements that define the book (e.g., Forbidden Love, Enemies-to-Lovers, Chosen One, Heist Gone Wrong). Use relevant emojis for each one.",
    "Write a single, high-concept, compelling sentence (under 30 words) that captures the central conflict, primary stakes, and genre of the story.",
    "Create a three-sentence synopsis that follows this structure: Sentence 1 (The inciting incident/main character's starting struggle), Sentence 2 (The central conflict/main relationship introduction), Sentence 3 (The primary stakes/mystery/emotional core).",
    "Generate five unique, deep-POV marketing blurbs (200-250 words each). Each blurb must focus on a different key marketing angle of the story (e.g., Hero's inner conflict, Heroine's emotional journey, the world/mystery, the central relationship dynamic, the inciting incident).",
    "Analyze the five generated blurbs and select the 'Best Choice', providing a brief rationale (1-2 sentences) explaining why it is the strongest for market positioning and widest appeal.",
    "Create a list of 10 short, punchy, and emotionally resonant taglines/story hooks (5-10 words each) for use in social media and advertising.",
    "Develop 10 long-tail Backend Keywords (search phrases) that accurately describe the book's genre, themes, and tropes.",
    "Provide the 3 best-fit Kindle Categories for the book (using the full path, e.g., Kindle eBooks > Fiction > Genre > Subgenre).",
    "Provide the 5 most relevant BISAC/Thema Codes.",
    "Provide a Rationale (1-2 sentences) explaining why the chosen categories and codes are the best strategic fit for reaching the target reader.",
    "Generate 5 Subtitle/SEO Metadata Suggestions and specify the single Best Choice among them.",
    "Identify 3-5 Unique Selling Points (Marketing Hooks) that leverage the core emotional or plot elements of the book. For each hook, provide: * A short Description (1-3 sentences). * Reader Match Profile (Describe the ideal reader attracted by this hook). * Reach This Reader By (A specific social platform/targeting strategy). * 3-5 Comparable Titles (Recent, genre-relevant, list Title/Author). * A Specific Marketing Idea (A detailed, actionable social media post/ad concept).",
    "Outline a high-level, platform-specific Social Media Strategy for promotion. Detail the required content format, tone, and goals for Instagram, TikTok, and Facebook.",
    "Include a short list of 3 key things to Avoid in the book's promotion (e.g., tone, plot spoilers, graphic images).",
    "Generate 5 actionable post ideas for each format below. For each idea, specify the posting platform(s) (Instagram/Facebook/TikTok). * Static Images: Include a suggested visual and specific text overlay/quote. * Carousels: Include a multi-slide theme and content structure. * Slideshows/Reels/Videos: Include an aesthetic note (mood, visual style) and key text-on-screen concepts.",
    "Write five complete Facebook/Meta Ads (A/B testing ready). Each ad should have: * A unique Emotional/Plot Focus (e.g., 'Hero's Trauma,' 'High-stakes Mystery'). * The Blurb Number (from prompt 6) it pairs best with. * A concise, attention-grabbing Headline (under 10 words). * Engaging Ad Copy (5-8 sentences, including a strong hook and clear Call to Action).",
    "Curate an Excerpt Library by identifying: * 3 Short Excerpts (1-3 sentences each) with a suggested Context/Use Case. * 3 Slideshow Excerpt Kits (4-8 text slides for a video) with an Aesthetic Note (e.g., 'Gritty and industrial'). * 1 Long Excerpt (1-2 paragraphs) with a suggested Context/Use Case.",
    "Provide a brief Final Sensitivity Review. Identify the book's core sensitive themes (e.g., trauma, grief, addiction). Then, provide a statement (1-2 sentences) confirming that the marketing approach focuses on resilience and healing/resolution and avoids exploitation or sensationalism."
]

GEMINI_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini 2.5 flash-lite",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
]

class BookMarketingGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Gemini Book Marketing Generator")
        self.root.geometry("800x700")
        self.root.minsize(700, 600)
        
        self.selected_files = []
        self.output_path = tk.StringVar()
        self.api_key = tk.StringVar(value=os.environ.get("GOOGLE_API_KEY", ""))
        self.selected_model = tk.StringVar(value=GEMINI_MODELS[0])
        self.is_running = False
        self.cancel_requested = False
        
        self.create_widgets()
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Title
        title = ttk.Label(main_frame, text="📚 Gemini Book Marketing Generator", font=("Helvetica", 16, "bold"))
        title.grid(row=0, column=0, pady=(0, 15), sticky="w")
        
        # API Key Section
        api_frame = ttk.LabelFrame(main_frame, text="Google API Key", padding="10")
        api_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        api_frame.columnconfigure(0, weight=1)
        
        api_entry = ttk.Entry(api_frame, textvariable=self.api_key, show="*", width=60)
        api_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        env_label = ttk.Label(api_frame, text="(Or set GOOGLE_API_KEY environment variable)", font=("Helvetica", 9))
        env_label.grid(row=1, column=0, sticky="w", pady=(5, 0))
        
        # Model Selection
        model_frame = ttk.LabelFrame(main_frame, text="Gemini Model", padding="10")
        model_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        model_frame.columnconfigure(0, weight=1)
        
        model_combo = ttk.Combobox(model_frame, textvariable=self.selected_model, values=GEMINI_MODELS, state="readonly", width=40)
        model_combo.grid(row=0, column=0, sticky="w")
        
        # File Selection
        file_frame = ttk.LabelFrame(main_frame, text="Input Files", padding="10")
        file_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        file_frame.columnconfigure(0, weight=1)
        
        btn_frame = ttk.Frame(file_frame)
        btn_frame.grid(row=0, column=0, sticky="ew")
        
        select_btn = ttk.Button(btn_frame, text="Select Book Files...", command=self.select_files)
        select_btn.pack(side="left", padx=(0, 10))
        
        clear_btn = ttk.Button(btn_frame, text="Clear Selection", command=self.clear_files)
        clear_btn.pack(side="left")
        
        self.file_listbox = tk.Listbox(file_frame, height=5, selectmode=tk.EXTENDED)
        self.file_listbox.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        
        scrollbar = ttk.Scrollbar(file_frame, orient="vertical", command=self.file_listbox.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", pady=(10, 0))
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Output Path
        output_frame = ttk.LabelFrame(main_frame, text="Output Directory", padding="10")
        output_frame.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        output_frame.columnconfigure(0, weight=1)
        
        output_entry = ttk.Entry(output_frame, textvariable=self.output_path, width=60)
        output_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        browse_btn = ttk.Button(output_frame, text="Browse...", command=self.browse_output)
        browse_btn.grid(row=0, column=1)
        
        # Progress Section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=5, column=0, sticky="ew", pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_label = ttk.Label(progress_frame, text="Ready")
        self.progress_label.grid(row=0, column=0, sticky="w")
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode="determinate", length=400)
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
        self.log_text.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")
        
    def call_model(self, model_name, prompt):
        """Call the installed google.generativeai API in a resilient way.

        Different versions of the library expose different helpers. Try common
        entry points and normalize the response into a plain string.
        """
        # Preferred: module-level convenience function
        try:
            if hasattr(genai, "generate_text"):
                resp = genai.generate_text(model=model_name, prompt=prompt)
                if isinstance(resp, dict):
                    cands = resp.get("candidates") or resp.get("outputs")
                    if cands and isinstance(cands, (list, tuple)):
                        first = cands[0]
                        if isinstance(first, dict):
                            return first.get("output") or first.get("content") or first.get("text") or str(first)
                        return str(first)
                    return resp.get("text") or str(resp)

            # Older or alternate API shape: a GenerativeModel class
            if hasattr(genai, "GenerativeModel"):
                try:
                    model = genai.GenerativeModel(model_name)
                except Exception:
                    model = genai.GenerativeModel()

                if hasattr(model, "generate_text"):
                    r = model.generate_text(prompt)
                    return getattr(r, "text", str(r))
                if hasattr(model, "generate_content"):
                    r = model.generate_content(prompt)
                    return getattr(r, "text", str(r))

            # Fallback: try a generic generate function
            if hasattr(genai, "generate"):
                resp = genai.generate(model=model_name, prompt=prompt)
                if isinstance(resp, dict):
                    return resp.get("output") or resp.get("text") or str(resp)
                return str(resp)

            raise ModelCallError("No supported generation method available in google.generativeai module.")
        except Exception as e:
            raise ModelCallError(str(e))
        
    def select_files(self):
        filetypes = [
            ("Text files", "*.txt"),
            ("PDF files", "*.pdf"),
            ("All files", "*.*")
        ]
        files = filedialog.askopenfilenames(title="Select Book Files", filetypes=filetypes)
        if files:
            for f in files:
                if f not in self.selected_files:
                    self.selected_files.append(f)
                    self.file_listbox.insert(tk.END, Path(f).name)
            self.log(f"Added {len(files)} file(s)")
            
    def clear_files(self):
        self.selected_files = []
        self.file_listbox.delete(0, tk.END)
        self.log("Cleared file selection")
        
    def browse_output(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_path.set(directory)
            self.log(f"Output directory: {directory}")
            
    def validate_inputs(self):
        if not self.api_key.get().strip():
            messagebox.showerror("Error", "Please enter your Google API Key or set the GOOGLE_API_KEY environment variable.")
            return False
        if not self.selected_files:
            messagebox.showerror("Error", "Please select at least one book file.")
            return False
        if not self.output_path.get().strip():
            messagebox.showerror("Error", "Please select an output directory.")
            return False
        if not os.path.isdir(self.output_path.get()):
            try:
                os.makedirs(self.output_path.get())
            except Exception as e:
                messagebox.showerror("Error", f"Cannot create output directory: {e}")
                return False
        return True
    
    def start_processing(self):
        if not self.validate_inputs():
            return
        self.is_running = True
        self.cancel_requested = False
        self.start_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress_bar["value"] = 0
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
                self.log("google.generativeai module is not installed.")
                self.root.after(0, lambda: messagebox.showerror("Error", "Required module 'google.generativeai' is not installed. Install with: pip install google-generative-ai"))
                return

            # Configure API key if available
            if hasattr(genai, "configure"):
                try:
                    genai.configure(api_key=self.api_key.get().strip())
                except Exception:
                    # Some versions use a different configure interface or environment variable; ignore here
                    pass
            self.log(f"Using model: {self.selected_model.get()}")
            
            total_files = len(self.selected_files)
            total_prompts = len(MARKETING_PROMPTS)
            total_ops = total_files * total_prompts
            current_op = 0
            
            for file_idx, file_path in enumerate(self.selected_files):
                if self.cancel_requested:
                    self.log("Processing cancelled by user.")
                    break
                    
                file_name = Path(file_path).stem
                self.log(f"Processing file {file_idx + 1}/{total_files}: {file_name}")
                
                # Read file content
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        book_content = f.read()
                except UnicodeDecodeError:
                    with open(file_path, "r", encoding="latin-1") as f:
                        book_content = f.read()
                except Exception as e:
                    self.log(f"Error reading {file_name}: {e}")
                    continue
                
                # Process each prompt
                results = []
                for prompt_idx, prompt in enumerate(MARKETING_PROMPTS):
                    if self.cancel_requested:
                        break
                        
                    current_op += 1
                    self.root.after(0, lambda c=current_op, t=total_ops, d=f"Prompt {prompt_idx + 1}/{total_prompts}": 
                                   self.update_progress(c, t, d))
                    
                    try:
                        full_prompt = f"""You are a professional book marketing expert. Based on the following book content, please complete this task:

{prompt}

BOOK CONTENT:
{book_content[:100000]}  # Limit content to avoid token limits
"""

                        # Retry logic for transient errors (e.g., 429 quota errors)
                        max_retries = 3
                        delay = 1.0
                        success = False
                        result_text = None

                        for attempt in range(1, max_retries + 1):
                            try:
                                result_text = self.call_model(self.selected_model.get(), full_prompt)
                                success = True
                                break
                            except ModelCallError as mce:
                                err_str = str(mce)
                                # Decide if retrying makes sense: treat quota/429 and transient network errors as retryable
                                retryable = False
                                low = err_str.lower()
                                if "429" in err_str or "resource has been exhausted" in low or "quota" in low or "rate limit" in low or "timeout" in low or "temporar" in low:
                                    retryable = True
                                else:
                                    # For unknown errors, still allow a couple attempts
                                    retryable = True

                                self.log(f"  ⚠️ Model error on attempt {attempt}/{max_retries}: {err_str}")
                                if attempt < max_retries and retryable:
                                    self.log(f"  → Retrying in {delay}s...")
                                    time.sleep(delay)
                                    delay *= 2
                                    continue
                                else:
                                    # Final failure after retries: capture the error message
                                    result_text = f"Error calling model after {attempt} attempt(s): {err_str}"
                                    success = False
                                    break

                        if success and result_text:
                            results.append((prompt_idx + 1, prompt, result_text))
                            self.log(f"  ✓ Completed prompt {prompt_idx + 1}/{total_prompts}")
                        else:
                            results.append((prompt_idx + 1, prompt, result_text or "No response generated."))
                            self.log(f"  ✗ Failed prompt {prompt_idx + 1}/{total_prompts}: {result_text}")

                    except Exception as e:
                        error_msg = f"Error: {str(e)}"
                        results.append((prompt_idx + 1, prompt, error_msg))
                        self.log(f"  ✗ Error on prompt {prompt_idx + 1}: {e}")
                
                if not self.cancel_requested:
                    # Generate markdown report
                    report = self.generate_report(file_name, results)
                    output_file = Path(self.output_path.get()) / f"{file_name}_Marketing_Report.md"
                    
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(report)
                    
                    self.log(f"✓ Saved report: {output_file.name}")
            
            if not self.cancel_requested:
                self.log("=" * 50)
                self.log("Processing complete!")
                self.root.after(0, lambda: messagebox.showinfo("Complete", "All files processed successfully!"))
                
        except Exception as e:
            self.log(f"Fatal error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Processing failed: {e}"))
        finally:
            self.is_running = False
            self.root.after(0, self.reset_ui)
            
    def reset_ui(self):
        self.start_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self.progress_label.configure(text="Ready")
        self.progress_detail.configure(text="")
        
    def generate_report(self, book_name, results):
        report = f"""# 📚 Gemini Pro Book Marketing Content Report

**Book:** {book_name}  
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Model:** {self.selected_model.get()}

---

"""
        for prompt_num, prompt, result in results:
            report += f"""## {prompt_num}. Prompt {prompt_num}

**Task:** {prompt}

### Response:

{result}

---

"""
        report += """## 💡 Note on File Format

This report is in **Markdown (.md)** format. You can open it with any text editor or word processor. For a formatted Word document, open the file and then use 'File > Save As' to save it as a '.docx' file. The headings, bold text, and lists will be preserved!
"""
        return report


def main():
    root = tk.Tk()
    
    # Set theme
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")
    
    app = BookMarketingGenerator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
