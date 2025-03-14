import unittest
from pathlib import Path
from unittest import mock

from document_search.exporter import ResultExporter
from document_search.models import SearchMatch


class TestResultExporter(unittest.TestCase):
    def setUp(self):
        self.search_term = "test query"
        self.directory = Path("/test/directory")
        self.exporter = ResultExporter(self.search_term, self.directory)

        # Mock timestamp to make tests deterministic
        self.timestamp = "20240101_120000"
        self.exporter.timestamp = self.timestamp
        self.exporter.formatted_date = "2024-01-01 12:00:00"

        # Sample test data - use Path objects for file_path
        self.test_matches = [
            SearchMatch(
                file_path=Path("doc1.pdf"),
                page_or_section="Page 1",
                context="This is a test context with query terms",
                match_positions=[(20, 25)],
            ),
            SearchMatch(
                file_path=Path("doc1.pdf"),
                page_or_section="Page 2",
                context="Another test context",
                match_positions=[(8, 12)],
            ),
            SearchMatch(
                file_path=Path("doc2.docx"),
                page_or_section="Section 3",
                context="Different document match",
                match_positions=[(0, 9)],
            ),
        ]

    def test_get_export_path(self):
        """Test export path generation with correct formatting."""
        # Spaces are converted to underscores during sanitization
        expected_path = self.exporter.script_dir / f"search_test_query_{self.timestamp}.html"
        self.assertEqual(self.exporter._get_export_path("html"), expected_path)

    @mock.patch("pathlib.Path.open", new_callable=mock.mock_open)
    def test_export_html(self, mock_open):
        """Test HTML export format and content structure."""
        self.exporter.export_html(self.test_matches)

        # Check that file was opened for writing
        mock_open.assert_called_once()

        # Check HTML content structure
        write_calls = mock_open().write.call_args_list
        content = "".join(call.args[0] for call in write_calls)

        self.assertIn("<title>Search Results: test query</title>", content)
        # Check for actual highlighted portions instead of "query"
        self.assertIn("<mark>xt wi</mark>", content)  # From first match
        self.assertIn("<mark>test</mark>", content)  # From second match
        self.assertIn("<mark>Different</mark>", content)  # From third match
        self.assertIn("<h2>doc1.pdf</h2>", content)
        self.assertIn("<h2>doc2.docx</h2>", content)

    @mock.patch("pathlib.Path.open", new_callable=mock.mock_open)
    def test_export_markdown(self, mock_open):
        """Test Markdown export format and structure."""
        self.exporter.export_markdown(self.test_matches)

        write_calls = mock_open().write.call_args_list
        content = "".join(call.args[0] for call in write_calls)

        self.assertIn('# Search Results: "test query"', content)
        self.assertIn("## doc1.pdf", content)
        self.assertIn("### Page 1", content)
        self.assertIn("```\nThis is a test context with query terms\n```", content)

    @mock.patch("pathlib.Path.open", new_callable=mock.mock_open)
    def test_export_text(self, mock_open):
        """Test plain text export format."""
        self.exporter.export_text(self.test_matches)

        write_calls = mock_open().write.call_args_list
        content = "".join(call.args[0] for call in write_calls)

        self.assertIn('Search Results: "test query"', content)
        self.assertIn("=" * 50, content)
        self.assertIn("Page 1:", content)
        self.assertIn("This is a test context with query terms", content)

    def test_export_with_invalid_format(self):
        """Test export with invalid format returns None."""
        result = self.exporter.export(self.test_matches, "invalid_format")
        self.assertIsNone(result)

    def test_export_with_empty_results(self):
        """Test export with empty results returns None."""
        result = self.exporter.export([], "html")
        self.assertIsNone(result)

    @mock.patch("document_search.exporter.ResultExporter.export_html")
    def test_export_dispatches_to_html(self, mock_html):
        """Test export dispatches to the correct export method for HTML."""
        self.exporter.export(self.test_matches, "html")
        mock_html.assert_called_once_with(self.test_matches)

    @mock.patch("document_search.exporter.ResultExporter.export_markdown")
    def test_export_dispatches_to_markdown(self, mock_md):
        """Test export dispatches to the correct method for both markdown formats."""
        self.exporter.export(self.test_matches, "markdown")
        mock_md.assert_called_once_with(self.test_matches)

        mock_md.reset_mock()
        self.exporter.export(self.test_matches, "md")
        mock_md.assert_called_once_with(self.test_matches)

    @mock.patch("document_search.exporter.ResultExporter.export_text")
    def test_export_dispatches_to_text(self, mock_text):
        """Test export dispatches to the correct method for both text formats."""
        self.exporter.export(self.test_matches, "text")
        mock_text.assert_called_once_with(self.test_matches)

        mock_text.reset_mock()
        self.exporter.export(self.test_matches, "txt")
        mock_text.assert_called_once_with(self.test_matches)

    def test_sanitize_long_search_term_in_filename(self):
        """Test that long search terms are truncated in export filenames."""
        exporter = ResultExporter(
            "a very long search term that should be truncated in the filename", self.directory
        )
        exporter.timestamp = self.timestamp

        path = exporter._get_export_path("html")
        filename = path.name

        self.assertLessEqual(
            len(filename),
            100,
            f"Filename length exceeds 100 characters. Actual filename: '{filename}'",
        )
        self.assertTrue(
            filename.startswith("search_a_very_long_search_term"),
            f"Filename does not start with expected prefix. Actual filename: '{filename}'",
        )
        self.assertTrue(
            filename.endswith(f"{self.timestamp}.html"),
            f"Filename does not end with expected suffix. Actual filename: '{filename}'",
        )
