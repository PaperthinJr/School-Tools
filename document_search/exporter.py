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
import sys
from pathlib import Path
from typing import Optional

from .constants import EXPORT_FORMATS
from .models import SearchMatch
from .utils import sanitize_filename, wrap_text


def get_exe_directory() -> Optional[Path]:
    """Returns the directory where the .exe is located, or None if running as a Python script."""
    if getattr(sys, "frozen", False):  # Running as PyInstaller .exe
        return Path(sys.executable).parent.resolve()
    return None  # Running as a normal Python package


class ResultExporter:
    """
    Export search results to various document formats.
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
        self.formatted_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Set once

        # If running as an .exe, export to the .exe directory; otherwise, use the script directory
        exe_directory = get_exe_directory()
        self.export_dir = exe_directory if exe_directory else Path(__file__).parent.resolve()

    def _get_export_path(self, extension: str) -> Path:
        """
        Generate export file path inside the .exe directory if running as .exe,
        or inside the script directory if running normally.

        Args:
            extension: File extension without leading dot (e.g., 'html')

        Returns:
            Path object for the output file
        """
        sanitized_term = sanitize_filename(self.search_term, max_length=30)
        return self.export_dir / f"export_{sanitized_term}_{self.timestamp}.{extension}"

    def export_html(self, results: list[SearchMatch]) -> Path:
        output_path = self._get_export_path("html")
        with output_path.open("w", encoding="utf-8") as f:
            f.write(
                f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Search Results: {html.escape(self.search_term)}</title>
        <style>
            :root {{
                --bg: #0d1117;
                --text: #c9d1d9;
                --accent: #58a6ff;
                --surface: #161b22;
                --border: #30363d;
                --highlight: #1f6feb;
            }}
            * {{
                box-sizing: border-box;
                scroll-behavior: smooth;
            }}
            body {{
                background: var(--bg);
                color: var(--text);
                font-family: system-ui, -apple-system, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 2rem;
                max-width: 1200px;
                margin: 0 auto;
            }}
            h1, h2, h3 {{
                color: #fff;
                margin-top: 1.5em;
            }}
            .header {{
                top: 0;
                background: var(--bg);
                padding: 1rem 0;
                border-bottom: 1px solid var(--border);
                z-index: 100;
            }}
            .result-file {{
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 1.5rem;
                margin: 1rem 0;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            mark {{
                background-color: var(--highlight);
                color: #fff;
                padding: 0.2em 0.4em;
                border-radius: 3px;
            }}
            .top-btn {{
                position: fixed;
                bottom: 2rem;
                right: 2rem;
                background: var(--accent);
                color: #fff;
                border: none;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                cursor: pointer;
                opacity: 0.8;
                transition: opacity 0.3s;
            }}
            .top-btn:hover {{
                opacity: 1;
            }}
            .meta {{
                display: grid;
                gap: 0.5rem;
                background: var(--surface);
                padding: 1rem;
                border-radius: 6px;
                margin: 1rem 0;
            }}
            code {{
                font-family: 'Consolas', monospace;
                background: #1b1f24;
                padding: 0.2em 0.4em;
                border-radius: 3px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Search Results</h1>
        </div>
        <div class="meta">
            <div><strong>Search Term:</strong> {html.escape(self.search_term)}</div>
            <div><strong>Directory:</strong> {html.escape(str(self.directory))}</div>
            <div><strong>Date:</strong> {self.formatted_date}</div>
        </div>
    """
            )

            current_file = None
            for result in results:
                file_path = Path(result.file_path)
                if current_file != file_path:
                    if current_file is not None:
                        f.write("</div>\n")  # Close previous result-file div
                    f.write(f'<div class="result-file"><h2>{html.escape(str(file_path))}</h2>\n')
                    current_file = file_path

                f.write(f"<h3>{html.escape(result.page_or_section or '')}</h3>\n")
                context_html = html.escape(result.context)
                for start, end in sorted(result.match_positions, reverse=True):
                    match_text = html.escape(result.context[start:end])
                    context_html = (
                        f"{context_html[:start]}<mark>{match_text}</mark>{context_html[end:]}"
                    )
                f.write(f"<p><code>{context_html}</code></p>\n")  # Removed </div>

            if current_file is not None:
                f.write("</div>\n")  # Close last result-file div

            f.write(
                """
        <button onclick="window.scrollTo({top: 0, behavior: 'smooth'})" class="top-btn">↑</button>
    </body>
    </html>"""
            )
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
