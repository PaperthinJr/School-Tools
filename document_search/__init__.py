"""
Document Search Package
=======================

This package provides functionality for searching for patterns in Word and PDF documents,
including both CLI and interactive modes, as well as exporting the results.
"""

__version__ = "1.0.0"  # Update version as needed

from .main import main as cli_main, run_search
from .interactive import interactive_main
from .searcher import execute_search, WordSearcher
from .exporter import ResultExporter
from .models import SearchMatch
from .constants import EXCLUDED_DIRS, DEFAULT_PATTERNS, EXPORT_FORMATS, MAX_WORKERS
from .utils import highlight_text, wrap_text, sanitize_filename, is_valid_directory

__all__ = [
    "__version__",
    "cli_main",
    "run_search",
    "interactive_main",
    "execute_search",
    "WordSearcher",
    "ResultExporter",
    "SearchMatch",
    "EXCLUDED_DIRS",
    "DEFAULT_PATTERNS",
    "EXPORT_FORMATS",
    "MAX_WORKERS",
    "highlight_text",
    "wrap_text",
    "sanitize_filename",
    "is_valid_directory",
]
