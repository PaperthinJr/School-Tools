"""
Data models for document search results.

This module contains dataclass definitions that represent search results from documents,
providing a structured way to pass match data between components.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class SearchMatch:
    """
    Represents a text match found during document searches.

    This class serves as a data transfer object between the search engine and result processors
    (like exporters). It contains all necessary metadata about where a match was found and
    its surrounding context.

    Attributes:
        file_path: Path to the document file containing the match.
        context: Text snippet surrounding the match for display purposes.
        page_or_section: Optional identifier for where in the document the match appears.
            For PDFs, typically a page number. For Word docs, could be section/paragraph.
            Perhaps None if location cannot be determined.
        match_positions: List of (start, end) index tuples indicating the exact position(s)
            of matched text within the context string. Used for highlighting in exports.
    """

    file_path: Path  # Absolute path to the document containing the match
    context: str  # Text surrounding the match with enough context to be meaningful
    page_or_section: Optional[str] = None  # Location identifier within document (if available)
    match_positions: List[Tuple[int, int]] = field(
        default_factory=list,  # Proper initialization for mutable default
        # Each tuple contains (start_index, end_index) within the context string
    )
