"""
Search functionality for document analysis.

This module provides tools for searching text patterns across Word and PDF documents,
with support for regular expressions, case sensitivity, and multithreading.
"""

import os
import re
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Optional, Set, Tuple

# Import from constants instead of duplicating dependency detection
from .constants import (
    DEFAULT_PATTERNS,
    DOCX_AVAILABLE,
    EXCLUDED_DIRS,
    MAX_WORKERS,
    PDF_AVAILABLE,
    TQDM_AVAILABLE,
    Document,
    PdfReader,
    tqdm,
)
from .exporter import ResultExporter
from .models import SearchMatch


class WordSearcher:
    """
    Searches for patterns in Word and PDF documents using multithreading.

    Provides methods to search for text patterns across multiple document types,
    with support for regular expressions, case sensitivity, and whole word matching.
    """

    def __init__(
        self,
        search_term: str,
        case_sensitive: bool = False,
        whole_word: bool = False,
        use_regex: bool = False,
        max_workers: Optional[int] = None,
    ) -> None:
        """
        Initialize the searcher with search parameters.

        Args:
            search_term: The text pattern to search for
            case_sensitive: Whether to match case exactly
            whole_word: Whether to match only whole words
            use_regex: Whether to interpret the search term as a regular expression
            max_workers: Maximum number of worker threads (defaults to CPU-based value)
        """
        self.search_term = search_term
        self.case_sensitive = case_sensitive
        self.whole_word = whole_word
        self.use_regex = use_regex
        self.max_workers = max_workers or MAX_WORKERS

        # Compile regex pattern
        self.pattern = self._compile_pattern()

    def _compile_pattern(self) -> re.Pattern[str]:
        """
        Compile the regex pattern based on user preferences.

        Returns:
            A compiled regular expression pattern
        """
        term = self.search_term if self.use_regex else re.escape(self.search_term)
        if self.whole_word:
            term = rf"\b{term}\b"
        flags = 0 if self.case_sensitive else re.IGNORECASE
        return re.compile(term, flags)

    def _find_matches_in_text(self, text: str) -> list[Tuple[int, int]]:
        """
        Find all matches in the given text.

        Args:
            text: The text to search within

        Returns:
            List of (start, end) positions for each match
        """
        return [(m.start(), m.end()) for m in self.pattern.finditer(text)]

    def _search_text(self, text: str) -> bool:
        """
        Check if the search term exists in the text.

        Args:
            text: The text to search within

        Returns:
            True if the pattern is found, False otherwise
        """
        return bool(self.pattern.search(text))

    def search_document(self, file_path: Path) -> list[SearchMatch]:
        """
        Searches for the pattern in a Word document.

        Args:
            file_path: Path to the Word document

        Returns:
            List of search matches found in the document
        """
        if not DOCX_AVAILABLE:
            print("Error: python-docx is not installed.")
            return []

        matches = []
        try:
            doc = Document(str(file_path))

            # Search in paragraphs
            for i, p in enumerate(doc.paragraphs):
                if self._search_text(p.text):
                    match_positions = self._find_matches_in_text(p.text)
                    matches.append(
                        SearchMatch(file_path, p.text, f"Paragraph {i + 1}", match_positions)
                    )

            # Search in tables
            for t_idx, table in enumerate(doc.tables):
                for r_idx, row in enumerate(table.rows):
                    for c_idx, cell in enumerate(row.cells):
                        if self._search_text(cell.text):
                            match_positions = self._find_matches_in_text(cell.text)
                            location = f"Table {t_idx + 1}, Row {r_idx + 1}, Column {c_idx + 1}"
                            matches.append(
                                SearchMatch(file_path, cell.text, location, match_positions)
                            )
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            if os.getenv("DEBUG"):
                traceback.print_exc()

        return matches

    def search_pdf(self, file_path: Path) -> list[SearchMatch]:
        """
        Searches for the pattern in a PDF document.

        Args:
            file_path: Path to the PDF document

        Returns:
            List of search matches found in the document
        """
        if not PDF_AVAILABLE:
            print("Error: pypdf is not installed.")
            return []

        matches = []
        try:
            with open(file_path, "rb") as file:
                reader = PdfReader(file)
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text and self._search_text(text):
                        match_positions = self._find_matches_in_text(text)
                        matches.append(
                            SearchMatch(file_path, text, f"Page {page_num + 1}", match_positions)
                        )
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            if os.getenv("DEBUG"):
                traceback.print_exc()

        return matches

    def process_file(self, file_path: Path) -> list[SearchMatch]:
        """
        Process a single file based on extension.

        Args:
            file_path: Path to the file to process

        Returns:
            List of search matches found in the file
        """
        if file_path.suffix.lower() == ".docx":
            return self.search_document(file_path)
        elif file_path.suffix.lower() == ".pdf":
            return self.search_pdf(file_path)
        return []

    @staticmethod
    def _collect_files(
        directory: Path, file_patterns: list[str], exclude_dirs: Set[str]
    ) -> list[Path]:
        """
        Collect all matching files in a directory, excluding specified folders.

        Args:
            directory: The root directory to start the search
            file_patterns: List of file patterns to match (e.g. "*.docx")
            exclude_dirs: Set of directory names to exclude from search

        Returns:
            List of Path objects for all matching files
        """
        files: list[Path] = []
        for root, dirs, _ in os.walk(directory):
            # Modify dirs in-place to prevent walking into excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            # Collect files matching each pattern
            for pattern in file_patterns:
                files.extend(Path(root).glob(pattern))

        return files

    def search_recursive(
        self,
        root_directory: Path,
        file_patterns: Optional[list[str]] = None,
        exclude_dirs: Optional[Set[str]] = None,
    ) -> list[SearchMatch]:
        """
        Recursively searches for patterns in documents across directories.

        Args:
            root_directory: The directory to start the search from
            file_patterns: List of file patterns to search (default: DEFAULT_PATTERNS)
            exclude_dirs: Set of directory names to exclude (default: EXCLUDED_DIRS)

        Returns:
            List of search matches found across all documents
        """
        file_patterns = file_patterns or DEFAULT_PATTERNS
        exclude_dirs = exclude_dirs or EXCLUDED_DIRS

        root_directory = root_directory.resolve()
        print(f"Searching in: {root_directory}")

        # Collect all files that match the patterns
        files = self._collect_files(root_directory, file_patterns, exclude_dirs)

        if not files:
            print("No matching files found.")
            return []

        all_matches = []

        # Use tqdm for progress display if available
        files_to_process = (
            tqdm(files, desc="Searching files", unit="file") if TQDM_AVAILABLE else files
        )

        # Process files concurrently using a thread pool
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self.process_file, file): file for file in files_to_process
            }

            for future in as_completed(future_to_file):
                matches = future.result()
                all_matches.extend(matches)

                # Print progress if tqdm is not available
                if not TQDM_AVAILABLE:
                    file_name = future_to_file[future].name
                    match_count = len(matches)
                    print(f"Processed: {file_name} - {match_count} matches found.")

        return all_matches


def execute_search(search_params: dict[str, Any]) -> list[SearchMatch]:
    """
    Executes the document search based on the given parameters.

    Args:
        search_params: Dictionary containing search configuration:
            - search_term: String to search for
            - case_sensitive: Whether to match case
            - whole_word: Whether to match whole words only
            - use_regex: Whether to use regex pattern matching
            - threads: Number of worker threads
            - directory: Root directory to search
            - file_patterns: Patterns of files to search
            - exclude: Directories to exclude
            - export_format: Format to export results (or None)

    Returns:
        List of search match results
    """
    start_time = time.time()

    # Initialize searcher
    searcher = WordSearcher(
        search_term=search_params["search_term"],
        case_sensitive=search_params["case_sensitive"],
        whole_word=search_params["whole_word"],
        use_regex=search_params["use_regex"],
        max_workers=search_params["threads"],
    )

    print("\nStarting search...")

    # Perform search
    results = searcher.search_recursive(
        root_directory=search_params["directory"],
        file_patterns=search_params["file_patterns"],
        exclude_dirs=search_params["exclude"],
    )

    # Display results in the terminal
    if results:
        unique_docs = len({match.file_path for match in results})
        print(f"\nFound {len(results)} matches in {unique_docs} documents.")
    else:
        print("\nNo matches found.")

    # Export results if requested
    if search_params["export_format"] and results:
        exporter = ResultExporter(search_params["search_term"], search_params["directory"])
        output_path = exporter.export(results, search_params["export_format"])
        if output_path:
            print(f"\nResults exported to: {output_path}")

    elapsed_time = time.time() - start_time
    print(f"\nSearch completed in {elapsed_time:.2f} seconds.")

    return results
