import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from document_search.interactive import display_results, get_user_input, interactive_menu
from document_search.models import SearchMatch


class TestInteractive(unittest.TestCase):
    def test_get_user_input_with_default(self):
        with patch("builtins.input", return_value=""):
            result = get_user_input("Enter something:", default="default_value")
            self.assertEqual(result, "default_value")

    def test_get_user_input_with_validation(self):
        with patch("builtins.input", side_effect=["invalid", "valid"]):
            with patch("builtins.print") as mock_print:
                result = get_user_input("Choose:", valid_options={"valid", "option"})
                self.assertEqual(result, "valid")
                mock_print.assert_called_once()

    def test_get_user_input_normal_input(self):
        with patch("builtins.input", return_value="user_input"):
            result = get_user_input("Enter something:")
            self.assertEqual(result, "user_input")

    @patch("document_search.interactive.get_user_input")
    @patch("builtins.input")
    def test_interactive_menu_basic_flow(self, mock_input, mock_get_input):
        # Setup mocks
        # Add an empty string to terminate the exclude directories loop
        mock_input.side_effect = ["search_term", ""]  # Added empty string here
        mock_get_input.side_effect = ["1", "n", "n", "n", "n", "y", "n"]

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_dir", return_value=True),
            patch("pathlib.Path.resolve", return_value=Path("/mock/path")),
        ):
            result = interactive_menu()

            self.assertEqual(result["search_term"], "search_term")
            self.assertFalse(result["case_sensitive"])
            self.assertFalse(result["whole_word"])
            self.assertFalse(result["use_regex"])
            self.assertIsNone(result["export_format"])

    @patch("document_search.interactive.get_user_input")
    @patch("builtins.input")
    def test_interactive_menu_with_export(self, mock_input, mock_get_input):
        # Setup mocks
        mock_input.side_effect = ["search_term", ""]  # Added empty string for exclude directories
        mock_get_input.side_effect = ["1", "n", "n", "n", "n", "y", "y", "1"]

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_dir", return_value=True),
            patch("pathlib.Path.resolve", return_value=Path("/mock/path")),
        ):
            result = interactive_menu()

            self.assertEqual(result["export_format"], "html")

    @patch("document_search.interactive.get_user_input")
    @patch("builtins.input")
    def test_interactive_menu_custom_directory(self, mock_input, mock_get_input):
        # Setup mocks
        mock_input.side_effect = ["search_term", "/custom/path", ""]  # Added empty string here
        mock_get_input.side_effect = ["3", "n", "n", "n", "n", "y", "n"]

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_dir", return_value=True),
            patch("pathlib.Path.resolve", return_value=Path("/custom/path")),
        ):
            result = interactive_menu()

            # Compare with Path object, not string
            self.assertEqual(result["directory"], Path("/custom/path"))

    @patch("document_search.interactive.get_user_input")
    @patch("builtins.input")
    def test_interactive_menu_custom_threads(self, mock_input, mock_get_input):
        # Setup mocks
        mock_input.side_effect = [
            "search_term",
            "",
            "4",
        ]  # Added empty string for exclude directories
        mock_get_input.side_effect = ["1", "n", "n", "n", "y", "y", "n"]

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_dir", return_value=True),
            patch("pathlib.Path.resolve", return_value=Path("/mock/path")),
        ):
            result = interactive_menu()

            self.assertEqual(result["threads"], 4)

    def test_display_results_with_matches(self):
        matches = [
            SearchMatch(
                file_path=Path("file1.txt"),
                page_or_section="Section 1",
                context="This is a match",
                match_positions=[(10, 15)],
            ),
            SearchMatch(
                file_path=Path("file1.txt"),
                page_or_section="Section 2",
                context="Another match",
                match_positions=[(8, 13)],
            ),
            SearchMatch(
                file_path=Path("file2.txt"),
                page_or_section="Page 1",
                context="Different file",
                match_positions=[(0, 9)],
            ),
        ]

        with patch("builtins.print") as mock_print:
            display_results(matches)
            # Verify print was called the expected number of times
            # 1 for summary + 2 files (2 headers) + 3 results (each with 4 print calls)
            self.assertGreaterEqual(mock_print.call_count, 15)

    @patch("document_search.interactive.interactive_menu")
    @patch("document_search.searcher.execute_search")
    @patch("document_search.interactive.display_results")
    @patch("document_search.interactive.ResultExporter")
    @patch("time.time")
    def test_interactive_main_with_export(
        self, mock_time, mock_exporter, mock_display, mock_search, mock_menu
    ):
        # Configure mocks
        mock_time.side_effect = [0, 10]  # Start and end times
        mock_matches = [MagicMock()]
        mock_menu.return_value = {
            "search_term": "test",
            "directory": Path("/test"),
            "export_format": "html",
            # Other params omitted for brevity
        }
        mock_search.return_value = mock_matches
        mock_exporter_instance = MagicMock()
        mock_exporter_instance.export.return_value = Path("/output.html")
        mock_exporter.return_value = mock_exporter_instance

        from document_search.interactive import interactive_main

        with patch("builtins.print") as mock_print:
            interactive_main()

            # Verify exporter was called
            mock_exporter.assert_called_once()
            mock_exporter_instance.export.assert_called_once()

            # Verify display_results was called with the search matches
            mock_display.assert_called_once_with(mock_matches)

            # Verify completion message was printed
            mock_print.assert_any_call("\nSearch completed in 10.00 seconds.")
