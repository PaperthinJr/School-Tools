"""
Constants and feature detection for document search program.

This module centralizes configuration values and detects optional dependencies at runtime,
enabling graceful feature degradation when libraries are unavailable.
"""

from multiprocessing import cpu_count
from typing import Any, Iterable, TypeVar

# Type variable for generic iterable
T = TypeVar("T")

# =================
# SEARCH CONSTANTS
# =================

# Skip these directories during recursive file searches
EXCLUDED_DIRS: set[str] = {".git", "__pycache__", "venv", ".venv"}

# File patterns that define searchable document types
DEFAULT_PATTERNS: list[str] = ["*.docx", "*.pdf"]

# =================
# SYSTEM SETTINGS
# =================

# Thread pool configuration
MIN_THREADS = 1
MAX_THREADS = 32

# Thread pool size scales with available CPU cores with a reasonable upper bound
MAX_WORKERS = min(MAX_THREADS, (cpu_count() or 4) + 4)

# =================
# OUTPUT OPTIONS
# =================

# Supported formats for exporting search results
EXPORT_FORMATS: set[str] = {"html", "markdown", "txt"}

# =================
# FEATURE DETECTION
# =================

# Document processing dependencies
try:
    # Microsoft Word document support (.docx)
    from docx import Document

    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

    class DocumentFallback:
        """Fallback Document class when python-docx is not installed."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            """Raise helpful error message when the library is missing."""
            raise ImportError(
                "python-docx is not installed. Install it with: pip install python-docx"
            )

    # Use the fallback when the real one isn't available
    Document = DocumentFallback  # type: ignore


try:
    # PDF document support
    from pypdf import PdfReader

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

    class PdfReaderFallback:
        """Fallback PdfReader class when pypdf is not installed."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            """Raise helpful error message when the library is missing."""
            raise ImportError("pypdf is not installed. Install it with: pip install pypdf")

    # Use the fallback when the real one isn't available
    PdfReader = PdfReaderFallback  # type: ignore


# UI enhancement dependencies
try:
    # Progress bar for long-running operations
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

    def tqdm_fallback(iterable: Iterable[T], **_: Any) -> Iterable[T]:
        """
        Fallback implementation for tqdm when the library is not installed.

        Args:
            iterable: The iterable to wrap
            **_: Progress bar configuration options (ignored in fallback)

        Returns:
            The original iterable without progress indication
        """
        # Fallback implementation ignores kwargs that would normally control the progress bar
        return iterable

    # Use the fallback when the real one isn't available
    tqdm = tqdm_fallback  # type: ignore


try:
    # Terminal text styling (colors, formatting)
    from colorama import Fore, Style, init

    init(autoreset=True)  # Configure colorama to automatically reset styles
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

    class ForeFallback:
        """Dummy color constants when colorama is not available."""

        BLACK = BLUE = CYAN = GREEN = LIGHTBLACK_EX = LIGHTBLUE_EX = ""
        LIGHTCYAN_EX = LIGHTGREEN_EX = LIGHTMAGENTA_EX = LIGHTRED_EX = ""
        LIGHTWHITE_EX = LIGHTYELLOW_EX = MAGENTA = RED = RESET = WHITE = YELLOW = ""

    class StyleFallback:
        """Dummy style constants when colorama is not available."""

        BRIGHT = DIM = NORMAL = RESET_ALL = ""

    def init_fallback(*_: Any, **__: Any) -> None:
        """No-op fallback for colorama's init function."""
        pass

    # Use the fallbacks when the real ones aren't available
    Fore = ForeFallback()  # type: ignore
    Style = StyleFallback()  # type: ignore
    init = init_fallback

# Explicitly export all public attributes
__all__ = [
    "T",
    "EXCLUDED_DIRS",
    "DEFAULT_PATTERNS",
    "MIN_THREADS",
    "MAX_THREADS",
    "MAX_WORKERS",
    "EXPORT_FORMATS",
    "DOCX_AVAILABLE",
    "PDF_AVAILABLE",
    "TQDM_AVAILABLE",
    "COLORAMA_AVAILABLE",
    "Document",
    "PdfReader",
    "tqdm",
    "Fore",
    "Style",
]
