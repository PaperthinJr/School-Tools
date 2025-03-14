import sys
import unittest
from typing import TypeVar
from unittest import mock


class TestConstants(unittest.TestCase):
    """Test the constants defined in constants.py."""

    def test_basic_constants(self):
        """Test the basic constants have expected types and values."""
        from document_search.constants import (
            DEFAULT_PATTERNS,
            EXCLUDED_DIRS,
            EXPORT_FORMATS,
            MAX_THREADS,
            MIN_THREADS,
        )

        # Check types
        self.assertIsInstance(EXCLUDED_DIRS, set)
        self.assertIsInstance(DEFAULT_PATTERNS, list)
        self.assertIsInstance(MIN_THREADS, int)
        self.assertIsInstance(MAX_THREADS, int)
        self.assertIsInstance(EXPORT_FORMATS, set)

        # Check values
        self.assertEqual(EXCLUDED_DIRS, {".git", "__pycache__", "venv", ".venv"})
        self.assertEqual(DEFAULT_PATTERNS, ["*.docx", "*.pdf"])
        self.assertEqual(MIN_THREADS, 1)
        self.assertEqual(MAX_THREADS, 32)
        self.assertEqual(EXPORT_FORMATS, {"html", "markdown", "txt"})

    def test_max_workers_calculation(self):
        """Test MAX_WORKERS is properly calculated based on CPU count."""
        # Mock cpu_count to return a known value
        with mock.patch("multiprocessing.cpu_count", return_value=4):
            # Need to reload the module to recalculate MAX_WORKERS
            if "document_search.constants" in sys.modules:
                del sys.modules["document_search.constants"]

            from document_search.constants import MAX_THREADS, MAX_WORKERS

            # MAX_WORKERS should be min(MAX_THREADS, cpu_count + 4)
            self.assertEqual(MAX_WORKERS, min(MAX_THREADS, 4 + 4))

    def test_max_workers_with_cpu_count_none(self):
        """Test MAX_WORKERS calculation when cpu_count returns None."""
        # Mock cpu_count to return None
        with mock.patch("multiprocessing.cpu_count", return_value=None):
            if "document_search.constants" in sys.modules:
                del sys.modules["document_search.constants"]

            from document_search.constants import MAX_WORKERS

            # Should fall back to 4 + 4 = 8 when cpu_count is None
            self.assertEqual(MAX_WORKERS, 8)


class TestFeatureDetection(unittest.TestCase):
    """Test feature detection and fallback behavior."""

    def setUp(self):
        """Clear module cache before each test."""
        # Clear the module from sys.modules to force reload
        if "document_search.constants" in sys.modules:
            del sys.modules["document_search.constants"]

    def test_docx_detection_available(self):
        """Test when python-docx is available."""
        # Mock the docx import to succeed
        with mock.patch.dict("sys.modules", {"docx": mock.MagicMock()}):
            from document_search.constants import DOCX_AVAILABLE

            self.assertTrue(DOCX_AVAILABLE)

    def test_docx_detection_unavailable(self):
        """Test when python-docx is not available."""
        # Mock the docx import to fail
        with mock.patch.dict("sys.modules", {"docx": None}):
            import builtins

            original_import = builtins.__import__
            with mock.patch(
                "builtins.__import__",
                side_effect=lambda name, *args: (
                    original_import(name, *args) if name != "docx" else raise_import_error()
                ),
            ):
                if "document_search.constants" in sys.modules:
                    del sys.modules["document_search.constants"]

                from document_search.constants import DOCX_AVAILABLE, Document

                self.assertFalse(DOCX_AVAILABLE)

                # Test the fallback raises a helpful error
                with self.assertRaises(ImportError) as context:
                    Document()
                self.assertIn("python-docx is not installed", str(context.exception))

    def test_pdf_detection(self):
        """Test PDF library detection."""
        # Test for pypdf available
        with mock.patch.dict("sys.modules", {"pypdf": mock.MagicMock()}):
            if "document_search.constants" in sys.modules:
                del sys.modules["document_search.constants"]

            from document_search.constants import PDF_AVAILABLE

            self.assertTrue(PDF_AVAILABLE)

        # Test for pypdf unavailable
        with mock.patch.dict("sys.modules", {"pypdf": None}):
            import builtins

            original_import = builtins.__import__
            with mock.patch(
                "builtins.__import__",
                side_effect=lambda name, *args: (
                    original_import(name, *args)
                    if name != "pypdf"
                    else (_ for _ in ()).throw(ImportError("Simulated ImportError for testing"))
                ),
            ):
                if "document_search.constants" in sys.modules:
                    del sys.modules["document_search.constants"]

                from document_search.constants import PDF_AVAILABLE, PdfReader

                self.assertFalse(PDF_AVAILABLE)

                # Test the fallback raises a helpful error
                with self.assertRaises(ImportError) as context:
                    PdfReader("test.pdf")
                self.assertIn("pypdf is not installed", str(context.exception))

    def test_tqdm_fallback(self):
        """Test tqdm fallback functionality."""
        # Test when tqdm is not available
        with mock.patch.dict("sys.modules", {"tqdm": None}):
            import builtins

            original_import = builtins.__import__
            with mock.patch(
                "builtins.__import__",
                side_effect=lambda name, *args: (
                    original_import(name, *args)
                    if name != "tqdm"
                    else (_ for _ in ()).throw(ImportError("Simulated ImportError for testing"))
                ),
            ):
                if "document_search.constants" in sys.modules:
                    del sys.modules["document_search.constants"]

                from document_search.constants import TQDM_AVAILABLE, tqdm

                self.assertFalse(TQDM_AVAILABLE)

                # Test fallback returns the original iterable
                test_list = [1, 2, 3]
                result = list(tqdm(test_list, desc="Test"))
                self.assertEqual(result, test_list)

    def test_colorama_fallback(self):
        """Test colorama fallback functionality."""
        # Remove 'colorama' from sys.modules to simulate its unavailability
        with mock.patch.dict("sys.modules", {"colorama": None}):
            if "document_search.constants" in sys.modules:
                del sys.modules["document_search.constants"]

            # Import constants after simulating the absence of colorama
            import document_search.constants as constants
            from document_search.constants import COLORAMA_AVAILABLE, Fore, Style

            # Verify that COLORAMA_AVAILABLE is False
            self.assertFalse(COLORAMA_AVAILABLE)

            # Verify that fallback attributes are empty strings
            self.assertEqual(Fore.RED, "")
            self.assertEqual(Style.BRIGHT, "")

            # Verify that the fallback init function is a no-op
            self.assertIsNone(constants.init())


class TestConstantsIntegrity(unittest.TestCase):
    def setUp(self):
        # Clear the module cache to force a fresh import
        if "document_search.constants" in sys.modules:
            del sys.modules["document_search.constants"]
        from document_search import constants

        self.constants = constants

    def test_public_api(self):
        """Test that __all__ contains the expected exported names."""
        expected_exports = {
            "T",  # Add this to match the TypeVar in constants.py
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
        }
        # Ensure __all__ exists and is a collection containing our expected names.
        self.assertTrue(hasattr(self.constants, "__all__"))
        self.assertTrue(expected_exports.issubset(set(self.constants.__all__)))

    def test_attribute_types(self):
        """Test the expected types of constants."""
        c = self.constants
        self.assertIsInstance(c.T, TypeVar)
        self.assertIsInstance(c.EXCLUDED_DIRS, set)
        self.assertIsInstance(c.DEFAULT_PATTERNS, list)
        self.assertIsInstance(c.MIN_THREADS, int)
        self.assertIsInstance(c.MAX_THREADS, int)
        self.assertIsInstance(c.MAX_WORKERS, int)
        self.assertIsInstance(c.EXPORT_FORMATS, set)


def raise_import_error():
    """Raise ImportError directly."""
    raise ImportError("Simulated ImportError for testing")


if __name__ == "__main__":
    unittest.main()
