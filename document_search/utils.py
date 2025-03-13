"""
Utility functions for the document search application.

This module contains helper functions for text manipulation, formatting,
and file operations used throughout the document search application.

Functions:
    highlight_text: Highlights text using ANSI colors.
    wrap_text: Wraps text to a specified width.
    sanitize_filename: Creates safe filenames by removing invalid characters.
    is_valid_directory: Validates that a path exists and is a directory.
"""


def highlight_text(text: str, positions: list[tuple[int, int]]) -> str:
    """
    Highlights matched text using ANSI color codes (if colorama is available).

    Args:
        text: The original text.
        positions: List of (start, end) index positions of the matched text.

    Returns:
        The text with highlighted matches.
    """
    try:
        from colorama import Fore, Style

        # Sort positions in reverse to avoid offsetting indices
        sorted_positions = sorted(positions, key=lambda x: x[0], reverse=True)
        highlighted_text = text

        for start, end in sorted_positions:
            if start < 0 or end > len(text) or start >= end:
                continue

            highlighted = f"{Fore.YELLOW}{Style.BRIGHT}{text[start:end]}{Style.RESET_ALL}"
            highlighted_text = highlighted_text[:start] + highlighted + highlighted_text[end:]

        return highlighted_text

    except ImportError:
        # If colorama isn't installed, return plain text
        return text


def wrap_text(text: str, max_width: int = 100) -> str:
    """
    Wraps text to the specified width without breaking words.

    Args:
        text: The text to wrap.
        max_width: The maximum line width.

    Returns:
        The wrapped text with line breaks.
    """
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue

        # Fix: Add type annotation for current_line
        current_line: list[str] = []
        current_length = 0

        for word in paragraph.split():
            word_length = len(word)

            if current_length + word_length + (1 if current_line else 0) <= max_width:
                if current_line:
                    current_length += 1  # Space before word
                current_line.append(word)
                current_length += word_length
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_length = word_length

        if current_line:
            lines.append(" ".join(current_line))

    return "\n".join(lines)


def sanitize_filename(filename: str, max_length: int = 50) -> str:
    """
    Sanitizes a filename by replacing invalid characters and truncating if necessary.

    Args:
        filename: The original filename.
        max_length: The maximum allowed length for the filename.

    Returns:
        A safe filename.
    """
    import re

    # Replace problematic characters AND spaces
    sanitized = re.sub(r'[\\/*?:"<>|\s]', "_", filename)

    # Truncate if needed
    if len(sanitized) > max_length:
        sanitized = sanitized[: max_length - 3] + "..."

    return sanitized


def is_valid_directory(path: str) -> bool:
    """
    Checks if a given path is a valid directory.

    Args:
        path: The path to check.

    Returns:
        True if it's a valid directory, False otherwise.
    """
    from pathlib import Path

    directory = Path(path)
    return directory.exists() and directory.is_dir()
