import tempfile
import unittest

from document_search.utils import highlight_text, is_valid_directory, sanitize_filename, wrap_text


class TestUtils(unittest.TestCase):
    def test_highlight_text_with_colorama(self):
        # Test that highlight_text returns text with ANSI codes when positions are provided
        text = "Hello world"
        positions = [(0, 5)]
        highlighted = highlight_text(text, positions)
        # When ANSI codes are present, the result should not equal the original text
        self.assertNotEqual(highlighted, text)
        self.assertIn("Hello", highlighted)
        # ANSI escape codes typically start with \x1b[
        self.assertIn("\x1b[", highlighted)

    def test_highlight_text_without_positions(self):
        # Calling highlight_text with no positions returns the original text
        text = "Test string"
        highlighted = highlight_text(text, [])
        self.assertEqual(highlighted, text)

    def test_wrap_text(self):
        # Verifies that wrap_text properly wraps text to a specified width
        text = "This is a test string that should be wrapped to a maximum width for validation."
        max_width = 20
        wrapped = wrap_text(text, max_width=max_width)
        # Each line should be less than or equal to max_width
        for line in wrapped.split("\n"):
            self.assertLessEqual(len(line), max_width)

    def test_sanitize_filename(self):
        # Checks that sanitize_filename removes invalid characters and truncates if too long
        filename = r"invalid\/:*?\"<>| file name.txt"
        sanitized = sanitize_filename(filename, max_length=30)
        # Ensure that no invalid characters remain in the sanitized filename
        for ch in r'\/:*?"<>| ':
            self.assertNotIn(ch, sanitized)
        self.assertLessEqual(len(sanitized), 30)

    def test_is_valid_directory(self):
        # Creates a temporary directory and validates that it is detected as valid
        with tempfile.TemporaryDirectory() as tmpdirname:
            self.assertTrue(is_valid_directory(tmpdirname))
        # A fake directory path should return False
        self.assertFalse(is_valid_directory("non_existing_dir"))


if __name__ == "__main__":
    unittest.main()
