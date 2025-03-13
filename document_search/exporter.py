"""
Search result export functionality for document search program.

This module provides capabilities to export search results to various document formats
including HTML, Markdown, and plain text. It handles the formatting, highlighting,
and organization of search results for readability and further analysis.

The module contains the ResultExporter class which manages file path generation,
content formatting, and appropriate structuring of output documents based on the
selected format. HTML exports include match highlighting, Markdown provides
structured documentation, and plain text offers a simple readable format.

This module works in conjunction with the search components to provide a complete
workflow from search execution to result presentation and persistence.
"""

import datetime
import html
from pathlib import Path
from typing import Optional

from .constants import EXPORT_FORMATS
from .models import SearchMatch
from .utils import sanitize_filename, wrap_text


class ResultExporter:
    """
    Export search results to various document formats.

    Transforms SearchMatch objects into readable documents with highlighted matches
    in formats including HTML, Markdown, and plain text. Handles proper formatting,
    file path generation, and text sanitization.
    """

    def __init__(self, search_term: str, directory: Path):
        """
        Initialize exporter with search parameters and configure output settings.

        Args:
            search_term: The term used for searching documents
            directory: Root directory where search was performed
        """
        self.search_term = search_term
        self.directory = directory.resolve()
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.script_dir = Path(__file__).parent.resolve()
        self.formatted_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Set once

    def _get_export_path(self, extension: str) -> Path:
        """
        Generate export file path with appropriate extension and sanitized filename.

        Args:
            extension: File extension without leading dot (e.g., 'html')

        Returns:
            Path object for the output file
        """
        sanitized_term = sanitize_filename(self.search_term, max_length=30)
        return self.script_dir / f"search_{sanitized_term}_{self.timestamp}.{extension}"

    def export_html(self, results: list[SearchMatch]) -> Path:
        """
        Export results to HTML with match highlighting and formatted structure.

        Args:
            results: List of search match objects

        Returns:
            Path to the exported HTML file
        """
        output_path = self._get_export_path("html")

        with output_path.open("w", encoding="utf-8") as f:
            f.write(
                f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Search Results: {html.escape(self.search_term)}</title>
    <style>
        mark {{ background-color: yellow; }}
        body {{ font-family: Arial, sans-serif; margin: 2em; }}
        h2 {{ margin-top: 1.5em; color: #2c3e50; }}
    </style>
</head>
<body>
    <h1>Search Results</h1>
    <p><strong>Search Term:</strong> {html.escape(self.search_term)}</p>
    <p><strong>Directory:</strong> {html.escape(str(self.directory))}</p>
    <p><strong>Date:</strong> {self.formatted_date}</p>
    <hr>
"""
            )

            current_file = None
            for result in results:
                file_path = Path(result.file_path)  # Ensure consistent handling of paths
                if current_file != file_path:
                    f.write(f"<h2>{html.escape(str(file_path))}</h2>\n")
                    current_file = file_path

                f.write(f"<h3>{html.escape(result.page_or_section or '')}</h3>\n")

                context_html = html.escape(result.context)
                for start, end in sorted(result.match_positions, reverse=True):
                    match_text = html.escape(result.context[start:end])
                    context_html = (
                        f"{context_html[:start]}<mark>{match_text}</mark>{context_html[end:]}"
                    )

                f.write(f"<p>{context_html}</p>\n")

            f.write("</body>\n</html>")

        return output_path

    def export_markdown(self, results: list[SearchMatch]) -> Path:
        """
        Export results to Markdown format with structured headings and code blocks.

        Args:
            results: List of search match objects

        Returns:
            Path to the exported Markdown file
        """
        output_path = self._get_export_path("md")

        with output_path.open("w", encoding="utf-8") as f:
            f.write(f'# Search Results: "{self.search_term}"\n\n')
            f.write(f"**Directory:** {self.directory}\n")
            f.write(f"**Date:** {self.formatted_date}\n\n")

            current_file = None
            for result in results:
                file_path = Path(result.file_path)
                if current_file != file_path:
                    f.write(f"\n## {file_path}\n\n")
                    current_file = file_path

                f.write(
                    f'### {result.page_or_section or ""}\n\n'
                    f"```\n{wrap_text(result.context)}\n```\n\n"
                )

        return output_path

    def export_text(self, results: list[SearchMatch]) -> Path:
        """
        Export results to plain text with visual separators for structure.

        Args:
            results: List of search match objects

        Returns:
            Path to the exported text file
        """
        output_path = self._get_export_path("txt")

        with output_path.open("w", encoding="utf-8") as f:
            f.write(f'Search Results: "{self.search_term}"\n{"=" * 50}\n\n')
            f.write(f"Directory: {self.directory}\n")
            f.write(f"Date: {self.formatted_date}\n\n")

            current_file = None
            for result in results:
                file_path = Path(result.file_path)
                if current_file != file_path:
                    f.write(f"\n{'=' * 50}\n{file_path}\n{'=' * 50}\n\n")
                    current_file = file_path

                f.write(
                    f'\n{result.page_or_section or ""}:\n{"-" * 40}\n'
                    f"{wrap_text(result.context)}\n{"-" * 40}\n"
                )

        return output_path

    def export(self, results: list[SearchMatch], format_type: str) -> Optional[Path]:
        """
        Export search results to the specified format.

        Args:
            results: List of search match objects
            format_type: Output format identifier (html, markdown/md, text/txt)

        Returns:
            Path to the exported file or None if export failed
        """
        if not results:
            print("No results to export.")
            return None

        format_type = format_type.lower()
        valid_formats = {"html", "markdown", "txt", "md", "text"}

        if format_type not in valid_formats:
            print(
                f"Unsupported export format: {format_type}. "
                f"Use one of: {', '.join(EXPORT_FORMATS)}"
            )
            return None

        export_methods = {
            "html": self.export_html,
            "markdown": self.export_markdown,
            "md": self.export_markdown,
            "text": self.export_text,
            "txt": self.export_text,
        }

        export_method = export_methods.get(format_type, lambda _: None)
        return export_method(results)
