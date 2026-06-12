import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
import queue
import sys
import os
import asyncio

# Import the scraping script without modifying it
import scrape_exam

class Redirector:
    """Redirects stdout and stderr to a thread-safe queue."""
    def __init__(self, log_queue):
        self.log_queue = log_queue
        
    def write(self, text):
        self.log_queue.put(text)
        
    def flush(self):
        pass

class ScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ExamTopics Scraper - GUI")
        self.root.geometry("750x550")
        
        # Make the UI look more modern
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')
            
        # UI Styling configurations
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=5)
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"))
        
        # Header
        header = ttk.Label(root, text="ExamTopics Automated Scraper", style="Header.TLabel")
        header.grid(row=0, column=0, columnspan=3, pady=(20, 10))
        
        # Exam Selection
        ttk.Label(root, text="Select Exam Code:").grid(row=1, column=0, padx=20, pady=10, sticky="e")
        self.exam_var = tk.StringVar()
        self.exam_cb = ttk.Combobox(root, textvariable=self.exam_var, values=["AZ-900", "AZ-204", "AZ-400"], font=("Segoe UI", 10))
        self.exam_cb.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self.exam_cb.current(0)
        
        # Output Directory
        ttk.Label(root, text="Output Folder:").grid(row=2, column=0, padx=20, pady=10, sticky="e")
        
        # Default to an 'output' folder in the current directory
        default_out = os.path.join(os.getcwd(), "output")
        self.out_var = tk.StringVar(value=default_out)
        
        self.out_entry = ttk.Entry(root, textvariable=self.out_var, state="readonly", font=("Segoe UI", 10))
        self.out_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        
        self.browse_btn = ttk.Button(root, text="Browse...", command=self.browse_folder)
        self.browse_btn.grid(row=2, column=2, padx=(10, 20), pady=10)
        
        # Control Buttons Frame
        btn_frame = ttk.Frame(root)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=(15, 5))
        
        self.start_btn = ttk.Button(btn_frame, text="▶ Start Scraping", command=self.start_scraping)
        self.start_btn.pack(side=tk.LEFT, padx=10)
        
        self.stop_btn = ttk.Button(btn_frame, text="⏹ Stop", command=self.stop_scraping, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        # Log Window
        ttk.Label(root, text="Application Logs:").grid(row=4, column=0, columnspan=3, padx=20, sticky="w")
        
        self.log_text = scrolledtext.ScrolledText(root, state='disabled', height=15, font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4")
        self.log_text.grid(row=5, column=0, columnspan=3, padx=20, pady=(5, 20), sticky="nsew")
        
        # Configure grid expansion
        root.grid_columnconfigure(1, weight=1)
        root.grid_rowconfigure(5, weight=1)
        
        # Thread-safe logging queue
        self.log_queue = queue.Queue()
        
        # Redirect stdout and stderr
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        redirector = Redirector(self.log_queue)
        sys.stdout = redirector
        sys.stderr = redirector
        
        # Start polling the log queue
        self.root.after(100, self.poll_queue)
        
    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.out_var.set(folder)
            
    def poll_queue(self):
        """Periodically checks the queue for new log messages and updates the text widget safely."""
        has_new_logs = False
        while not self.log_queue.empty():
            msg = self.log_queue.get()
            self.log_text.configure(state='normal')
            self.log_text.insert(tk.END, msg)
            has_new_logs = True
            
        if has_new_logs:
            self.log_text.see(tk.END)
            self.log_text.configure(state='disabled')
            
        self.root.after(100, self.poll_queue)
        
    def start_scraping(self):
        exam_code = self.exam_var.get().strip()
        output_dir = self.out_var.get().strip()
        
        if not exam_code:
            self.log_queue.put("ERROR: Please select or enter an exam code.\n")
            return
            
        if not output_dir:
            self.log_queue.put("ERROR: Please select an output directory.\n")
            return
            
        # Disable UI components during execution
        self.start_btn.config(state="disabled")
        self.browse_btn.config(state="disabled")
        self.exam_cb.config(state="disabled")
        self.stop_btn.config(state="normal")
        
        # Dynamically inject the chosen output directory into the scraper module
        # This fulfills the requirement of changing the output without editing scrape_exam.py
        scrape_exam.OUTPUT_DIR = output_dir
        
        self.log_queue.put(f"--- Starting Scraper ---\n")
        self.log_queue.put(f"Target Exam: {exam_code}\n")
        self.log_queue.put(f"Output Directory: {output_dir}\n\n")
        
        # Run Playwright in a background thread so the GUI doesn't freeze
        threading.Thread(target=self.run_scraper_thread, args=(exam_code,), daemon=True).start()
        
    def stop_scraping(self):
        if hasattr(self, 'scraper_task') and self.scraper_task is not None:
            self.log_queue.put("\n[INFO] Sending stop signal... please wait for browser to close.\n")
            self.stop_btn.config(state="disabled")
            if hasattr(self, 'loop') and self.loop is not None:
                self.loop.call_soon_threadsafe(self.scraper_task.cancel)

    def run_scraper_thread(self, exam_code):
        try:
            # Playwright requires a dedicated asyncio event loop when run in a thread
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.scraper_task = self.loop.create_task(scrape_exam.main(exam_code))
            self.loop.run_until_complete(self.scraper_task)
        except asyncio.CancelledError:
            self.log_queue.put("\n[INFO] Scraping process was stopped by user.\n")
        except Exception as e:
            self.log_queue.put(f"\n[CRITICAL ERROR] {str(e)}\n")
        finally:
            if hasattr(self, 'loop') and self.loop is not None:
                self.loop.close()
            self.scraper_task = None
            self.loop = None
            self.log_queue.put("\n--- Scraping Process Finished ---\n")
            # Safely re-enable UI via the main thread
            self.root.after(0, self.enable_ui)
            
    def enable_ui(self):
        self.start_btn.config(state="normal")
        self.browse_btn.config(state="normal")
        self.exam_cb.config(state="normal")
        self.stop_btn.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperGUI(root)
    
    # Ensure background threads are killed when the window is closed
    def on_closing():
        sys.stdout = app.original_stdout
        sys.stderr = app.original_stderr
        root.destroy()
        sys.exit(0)
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
