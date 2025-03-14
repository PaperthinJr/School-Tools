import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from pathlib import Path
from typing import Optional


class DocumentSearchGUI:
    def __init__(self, root, start_search_callback, export_callback):
        """
        Initialize the GUI.

        Args:
            root: The Tk root window.
            start_search_callback: Function to call when the search button is clicked.
            export_callback: Function to call when exporting results.
        """
        self.root = root
        self.root.title("Document Search")
        self.root.geometry("900x650")
        self.root.minsize(800, 600)

        # Callbacks
        self.start_search_callback = start_search_callback
        self.export_callback = export_callback

        # UI Components
        self.search_term_var = tk.StringVar()
        self.directory_var = tk.StringVar(value=str(Path.cwd()))
        self.case_sensitive_var = tk.BooleanVar(value=False)
        self.whole_word_var = tk.BooleanVar(value=False)
        self.regex_var = tk.BooleanVar(value=False)
        self.export_format_var = tk.StringVar(value="html")

        self.create_main_layout()

    def create_main_layout(self):
        """Sets up the main GUI layout."""
        self.create_search_frame()
        self.create_results_frame()
        self.create_status_bar()

    def create_search_frame(self):
        """Creates the search input section."""
        search_frame = ttk.LabelFrame(self.root, text="Search Setup")
        search_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(search_frame, text="Search Term:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_term_var, width=40)
        search_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(search_frame, text="Directory:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        dir_entry = ttk.Entry(search_frame, textvariable=self.directory_var, width=40)
        dir_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Button(search_frame, text="Browse...", command=self.browse_directory).grid(row=1, column=2, padx=5)

        self.search_btn = ttk.Button(search_frame, text="Start Search", command=self.start_search)
        self.search_btn.grid(row=2, column=0, padx=5, pady=5)

        self.export_btn = ttk.Button(search_frame, text="Export Results", command=self.export_results,
                                     state=tk.DISABLED)
        self.export_btn.grid(row=2, column=1, padx=5, pady=5)

        search_frame.columnconfigure(1, weight=1)

    def create_results_frame(self):
        """Creates the results display area."""
        results_frame = ttk.LabelFrame(self.root, text="Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, font=("Courier New", 10))
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.results_text.config(state=tk.DISABLED)

    def create_status_bar(self):
        """Creates a status bar at the bottom."""
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def browse_directory(self):
        """Opens a folder selection dialog."""
        dir_path = filedialog.askdirectory(initialdir=self.directory_var.get())
        if dir_path:
            self.directory_var.set(dir_path)

    def start_search(self):
        """Handles the search button click event."""
        search_term = self.search_term_var.get().strip()
        directory = Path(self.directory_var.get())

        if not search_term:
            messagebox.showwarning("Error", "Please enter a search term.")
            return
        if not directory.exists() or not directory.is_dir():
            messagebox.showwarning("Error", "Please select a valid directory.")
            return

        self.status_var.set("Searching...")
        self.start_search_callback(search_term, directory)

    def export_results(self):
        """Handles the export button click event."""
        self.export_callback(self.export_format_var.get())

    def update_results(self, results_text):
        """Updates the results display."""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, results_text)
        self.results_text.config(state=tk.DISABLED)
        self.export_btn.config(state=tk.NORMAL)

    def update_status(self, status_text):
        """Updates the status bar."""
        self.status_var.set(status_text)
