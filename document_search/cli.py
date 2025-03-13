"""
Command line argument parsing for document search program.

This module provides the CLI argument parsing functionality.
"""

import argparse
from pathlib import Path
from typing import Any

from .constants import DEFAULT_PATTERNS, EXCLUDED_DIRS, EXPORT_FORMATS


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments using argparse.

    Returns:
        Parsed arguments as a Namespace object.
    """
    parser = argparse.ArgumentParser(
        description="Search for patterns in Word and PDF documents.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("search_term", help="The word or pattern to search for", nargs="?")
    parser.add_argument("directory", help="The root directory to search in", nargs="?")

    parser.add_argument(
        "--case-sensitive", action="store_true", help="Enable case-sensitive matching"
    )
    parser.add_argument("--whole-word", action="store_true", help="Match whole words only")
    parser.add_argument("--regex", action="store_true", help="Use regular expression patterns")
    parser.add_argument("--threads", type=int, help="Set the number of worker threads (1-32)")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Exclude directories from search (can be used multiple times)",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Include PDF files in search (Word DOCX files always included)",
    )
    parser.add_argument(
        "--export",
        choices=EXPORT_FORMATS,
        help="Export results in specified format (html, markdown, txt)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Launch in interactive mode with a command menu",
    )

    return parser.parse_args()


def get_search_params(args: argparse.Namespace) -> dict[str, Any]:
    """
    Convert parsed arguments to a search parameters dictionary.

    Args:
        args: Parsed command-line arguments

    Returns:
        dictionary of search parameters for the search execution
    """
    return {
        "search_term": args.search_term,
        "directory": Path(args.directory).resolve() if args.directory else None,
        "case_sensitive": args.case_sensitive,
        "whole_word": args.whole_word,
        "use_regex": args.regex,
        "threads": args.threads,
        "exclude": EXCLUDED_DIRS | set(map(str, args.exclude)),  # Explicitly ensure str type
        "file_patterns": DEFAULT_PATTERNS if args.pdf else ["*.docx"],
        "export_format": args.export,
    }
