import argparse
import unittest
from pathlib import Path
from unittest.mock import patch

from document_search.cli import get_search_params, parse_arguments
from document_search.constants import DEFAULT_PATTERNS, EXCLUDED_DIRS


class TestCliArgumentParsing(unittest.TestCase):
    """Test command-line argument parsing functionality."""

    @patch("argparse.ArgumentParser.parse_args")
    def test_parse_minimal_arguments(self, mock_parse_args):
        """Test parsing with minimal arguments (search term and directory)."""
        # Setup mock return value
        mock_args = argparse.Namespace(
            search_term="test",
            directory="/path/to/search",
            case_sensitive=False,
            whole_word=False,
            regex=False,
            threads=None,
            exclude=[],
            pdf=False,
            export=None,
            interactive=False,
        )
        mock_parse_args.return_value = mock_args

        # Call the function
        args = parse_arguments()

        # Verify results
        self.assertEqual(args.search_term, "test")
        self.assertEqual(args.directory, "/path/to/search")
        self.assertFalse(args.case_sensitive)
        self.assertFalse(args.interactive)

    @patch("argparse.ArgumentParser.parse_args")
    def test_parse_all_arguments(self, mock_parse_args):
        """Test parsing with all arguments specified."""
        # Setup mock return value
        mock_args = argparse.Namespace(
            search_term="pattern",
            directory="/documents",
            case_sensitive=True,
            whole_word=True,
            regex=True,
            threads=4,
            exclude=["temp", "backup"],
            pdf=True,
            export="html",
            interactive=True,
        )
        mock_parse_args.return_value = mock_args

        # Call the function
        args = parse_arguments()

        # Verify results
        self.assertEqual(args.search_term, "pattern")
        self.assertEqual(args.directory, "/documents")
        self.assertTrue(args.case_sensitive)
        self.assertTrue(args.whole_word)
        self.assertTrue(args.regex)
        self.assertEqual(args.threads, 4)
        self.assertEqual(args.exclude, ["temp", "backup"])
        self.assertTrue(args.pdf)
        self.assertEqual(args.export, "html")
        self.assertTrue(args.interactive)


class TestGetSearchParams(unittest.TestCase):
    """Test conversion of parsed args to search parameters."""

    def test_search_params_minimal(self):
        """Test creating search parameters with minimal arguments."""
        args = argparse.Namespace(
            search_term="keyword",
            directory="/search/here",
            case_sensitive=False,
            whole_word=False,
            regex=False,
            threads=None,
            exclude=[],
            pdf=False,
            export=None,
        )

        params = get_search_params(args)

        self.assertEqual(params["search_term"], "keyword")
        self.assertEqual(params["directory"], Path("/search/here").resolve())
        self.assertFalse(params["case_sensitive"])
        self.assertFalse(params["whole_word"])
        self.assertFalse(params["use_regex"])
        self.assertEqual(params["file_patterns"], ["*.docx"])
        self.assertEqual(params["exclude"], EXCLUDED_DIRS)
        self.assertIsNone(params["export_format"])

    def test_search_params_full(self):
        """Test creating search parameters with all options."""
        args = argparse.Namespace(
            search_term="regex.*pattern",
            directory="C:/docs",
            case_sensitive=True,
            whole_word=True,
            regex=True,
            threads=8,
            exclude=["logs", "cache"],
            pdf=True,
            export="markdown",
        )

        params = get_search_params(args)

        self.assertEqual(params["search_term"], "regex.*pattern")
        self.assertEqual(params["directory"], Path("C:/docs").resolve())
        self.assertTrue(params["case_sensitive"])
        self.assertTrue(params["whole_word"])
        self.assertTrue(params["use_regex"])
        self.assertEqual(params["threads"], 8)
        self.assertEqual(params["file_patterns"], DEFAULT_PATTERNS)
        self.assertEqual(params["export_format"], "markdown")

        # Check that excluded dirs are properly combined
        expected_excludes = EXCLUDED_DIRS | {"logs", "cache"}
        self.assertEqual(params["exclude"], expected_excludes)

    def test_file_pattern_with_pdf_flag(self):
        """Test file patterns with PDF flag enabled/disabled."""
        args_no_pdf = argparse.Namespace(
            search_term="test",
            directory="/tmp",
            case_sensitive=False,
            whole_word=False,
            regex=False,
            threads=None,
            exclude=[],
            pdf=False,
            export=None,
        )

        args_with_pdf = argparse.Namespace(
            search_term="test",
            directory="/tmp",
            case_sensitive=False,
            whole_word=False,
            regex=False,
            threads=None,
            exclude=[],
            pdf=True,
            export=None,
        )

        params_no_pdf = get_search_params(args_no_pdf)
        params_with_pdf = get_search_params(args_with_pdf)

        self.assertEqual(params_no_pdf["file_patterns"], ["*.docx"])
        self.assertEqual(params_with_pdf["file_patterns"], DEFAULT_PATTERNS)


if __name__ == "__main__":
    unittest.main()
