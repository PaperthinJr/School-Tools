import unittest
from pathlib import Path

from document_search.models import SearchMatch


class TestSearchMatch(unittest.TestCase):
    def test_search_match_creation(self):
        """Test basic creation of a SearchMatch instance with required fields."""
        file_path = Path("/test/path.pdf")
        context = "This is a sample text with a match inside."

        match = SearchMatch(file_path=file_path, context=context)

        self.assertEqual(match.file_path, file_path)
        self.assertEqual(match.context, context)
        self.assertIsNone(match.page_or_section)
        self.assertEqual(match.match_positions, [])

    def test_search_match_with_optional_fields(self):
        """Test creation with all fields specified."""
        file_path = Path("/test/path.pdf")
        context = "This is a sample text with a match inside."
        page_or_section = "Page 5"
        match_positions = [(10, 15), (20, 25)]

        match = SearchMatch(
            file_path=file_path,
            context=context,
            page_or_section=page_or_section,
            match_positions=match_positions,
        )

        self.assertEqual(match.file_path, file_path)
        self.assertEqual(match.context, context)
        self.assertEqual(match.page_or_section, page_or_section)
        self.assertEqual(match.match_positions, match_positions)

    def test_match_positions_mutable_default(self):
        """Test that match_positions default is properly isolated between instances."""
        match1 = SearchMatch(file_path=Path("/test/doc1.pdf"), context="Example 1")
        match2 = SearchMatch(file_path=Path("/test/doc2.pdf"), context="Example 2")

        # Modify match positions for one instance
        match1.match_positions.append((5, 10))

        # Verify the other instance remains unchanged
        self.assertEqual(len(match1.match_positions), 1)
        self.assertEqual(len(match2.match_positions), 0)

    def test_path_is_path_object(self):
        """Test that file_path is a Path object."""
        # Create with string path but convert it to Path first
        string_path = "/test/path.txt"
        match = SearchMatch(file_path=Path(string_path), context="Example")
        self.assertIsInstance(match.file_path, Path)

        # Test with Path object directly
        path_obj = Path("/another/path.pdf")
        match2 = SearchMatch(file_path=path_obj, context="Example")
        self.assertIs(match2.file_path, path_obj)
