"""
Document Search Package
=======================

This package provides functionality for searching for patterns in Word and PDF documents,
including both CLI and interactive modes, as well as exporting the results.
"""

__version__ = "1.0.0"  # Update version as needed

from .constants import DEFAULT_PATTERNS, EXCLUDED_DIRS, EXPORT_FORMATS, MAX_WORKERS
from .exporter import ResultExporter
from .interactive import interactive_main
from .main import main as cli_main
from .main import run_search
from .models import SearchMatch
from .searcher import WordSearcher, execute_search
from .utils import highlight_text, is_valid_directory, sanitize_filename, wrap_text


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
