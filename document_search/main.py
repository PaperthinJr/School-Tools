"""
Main entry point for the document search application.

This module determines whether to run in interactive or CLI mode
and dispatches to the appropriate handlers.
"""

from typing import Any

from .cli import get_search_params, parse_arguments
from .interactive import interactive_main
from .searcher import execute_search


def run_search(search_params: dict[str, Any]) -> None:
    """
    Executes the document search based on the given parameters.

    Args:
        search_params: Dictionary of search parameters
    """
    execute_search(search_params)


def main() -> None:
    """
    Main entry point for the document search tool.
    Determines whether to run in interactive or CLI mode.
    """
    args = parse_arguments()

    # If no search term or directory provided, or interactive flag set, run interactive mode
    if args.interactive or not (args.search_term and args.directory):
        interactive_main()
    else:
        # Command-line mode
        search_params = get_search_params(args)
        run_search(search_params)


if __name__ == "__main__":
    main()
