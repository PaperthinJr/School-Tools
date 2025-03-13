"""
Interactive console interface for document search program.

This module provides a text-based user interface for configuring and executing document searches.
It handles user input collection, parameter validation, search execution, result display, and
optional export of search results to various formats. The interactive mode allows users to
configure all search parameters through guided prompts rather than command-line arguments.

The module serves as the main entry point for the interactive mode of the document search tool
and coordinates with other components like the searcher and exporter modules.
"""

import time
from pathlib import Path
from typing import Any, Collection, Dict, List, Optional, Union

from .constants import DEFAULT_PATTERNS, EXCLUDED_DIRS, EXPORT_FORMATS, MAX_THREADS, MIN_THREADS
from .exporter import ResultExporter
from .models import SearchMatch


def get_user_input(
    prompt: str, default: Optional[str] = None, valid_options: Optional[Collection[str]] = None
) -> Union[str, None]:
    """
    Get user input with validation and optional default value.

    Presents a prompt to the user and validates their input against provided options.
    Returns the default value if the user provides no input and a default is specified.

    Args:
        prompt: The message displayed to the user
        default: The default value if the user provides no input
        valid_options: A list of valid choices (optional)

    Returns:
        The user-provided input or the default value
    """
    while True:
        user_input = input(f"{prompt} ").strip()

        if not user_input and default is not None:
            return default

        if valid_options and user_input.lower() not in valid_options:
            print(f"Invalid choice. Options: {', '.join(valid_options)}")
            continue

        return user_input


def interactive_menu() -> Dict[str, Any]:
    """
    Display an interactive menu to configure search parameters.

    Walks the user through configuring all search parameters including directory selection,
    search options, file types, and result export preferences.

    Returns:
        A dictionary of configured search parameters
    """
    print("\n===== Interactive Document Search Tool =====\n")

    # Get search term
    search_term = input("Enter the word or pattern to search for: ").strip()
    while not search_term:
        search_term = input("Search term cannot be empty. Please enter a search term: ").strip()

    # Get directory
    script_dir = Path(__file__).parent.resolve()
    cwd = Path.cwd().resolve()

    print("\nDirectory options:")
    print(f"1. Script location: {script_dir}")
    print(f"2. Current working directory: {cwd}")
    print("3. Enter a custom path")

    choice = get_user_input(
        "Select directory option (1-3, default: 1):", default="1", valid_options={"1", "2", "3"}
    )

    if choice == "1":
        directory = script_dir
    elif choice == "2":
        directory = cwd
    else:
        directory = Path(input("Enter directory path: ").strip()).resolve()

    while not directory.exists() or not directory.is_dir():
        directory = Path(
            input("Invalid directory. Enter a valid directory path: ").strip()
        ).resolve()

    print(f"Search will be performed in: {directory}")

    # Search options
    case_sensitive = (
        get_user_input(
            "Enable case-sensitive matching? (y/N):", default="n", valid_options={"y", "n"}
        )
        == "y"
    )

    whole_word = (
        get_user_input("Match whole words only? (y/N):", default="n", valid_options={"y", "n"})
        == "y"
    )

    use_regex = (
        get_user_input(
            "Interpret the search term as a regex? (y/N):", default="n", valid_options={"y", "n"}
        )
        == "y"
    )

    # Exclude directories
    print("\nEnter directories to exclude (leave blank to finish):")
    exclude_dirs = set()
    while True:
        exclude_dir = input("Exclude directory (or press Enter to continue): ").strip()
        if not exclude_dir:
            break
        exclude_dirs.add(exclude_dir)

    # Add any pre-configured excluded directories
    exclude_dirs |= EXCLUDED_DIRS

    # Number of threads
    threads = None
    custom_threads = (
        get_user_input(
            "Specify number of worker threads? (y/N):", default="n", valid_options={"y", "n"}
        )
        == "y"
    )

    if custom_threads:
        while True:
            try:
                threads_prompt = f"Enter number of threads ({MIN_THREADS}-{MAX_THREADS}): "
                threads = int(input(threads_prompt).strip())
                if MIN_THREADS <= threads <= MAX_THREADS:
                    break
                print(f"Please enter a number between {MIN_THREADS} and {MAX_THREADS}.")
            except ValueError:
                print("Please enter a valid number.")

    # Include PDFs
    include_pdf = (
        get_user_input("Include PDF files in search? (Y/n):", default="y", valid_options={"y", "n"})
        == "y"
    )

    # Use DEFAULT_PATTERNS and filter out PDF if not requested
    file_patterns = [
        pattern for pattern in DEFAULT_PATTERNS if include_pdf or not pattern.endswith("pdf")
    ]

    # Export options
    export_format: Optional[str] = None
    if (
        get_user_input("Export results to a file? (y/N):", default="n", valid_options={"y", "n"})
        == "y"
    ):
        # Create display names for the export formats from EXPORT_FORMATS
        format_labels: Dict[str, str] = {
            "html": "HTML (with highlighted matches)",
            "markdown": "Markdown",
            "txt": "Plain Text",
        }

        # Print format options using available formats from EXPORT_FORMATS
        print("\nExport formats:")
        for i, fmt in enumerate(EXPORT_FORMATS, 1):
            print(f"{i}. {format_labels.get(fmt, fmt.capitalize())}")

        # Map numeric options to export format strings
        format_options = {str(i): fmt for i, fmt in enumerate(EXPORT_FORMATS, 1)}

        # Fixed type issue by ensuring export_choice is a valid string key
        export_choice = get_user_input(
            f"Select export format (1-{len(EXPORT_FORMATS)}, default: 1):",
            default="1",
            valid_options=set(format_options.keys()),
        )

        if export_choice is not None:  # Ensure the key is a string before dictionary lookup
            export_format = format_options[export_choice]

    return {
        "search_term": search_term,
        "directory": directory,
        "case_sensitive": case_sensitive,
        "whole_word": whole_word,
        "use_regex": use_regex,
        "threads": threads,
        "exclude": exclude_dirs,
        "file_patterns": file_patterns,
        "export_format": export_format,
    }


def display_results(results: List[SearchMatch]) -> None:
    """
    Format and display search results in the console with file grouping.

    Outputs each search result grouped by file, with separators and section information
    to improve readability in terminal output.

    Args:
        results: A list of SearchMatch objects containing match information
    """
    if results:
        # Calculate unique files for summary display
        unique_files = len({match.file_path for match in results})
        print(f"\nFound {len(results)} matches across {unique_files} documents:")

        current_file = None
        for result in results:
            if current_file != result.file_path:
                print(f"\n=== {result.file_path} ===")
                current_file = result.file_path

            print(f"\n{result.page_or_section or ''}:")
            print("-" * 40)
            print(result.context)
            print("-" * 40)
    else:
        print("\nNo matches found.")


def interactive_main() -> None:
    """
    Main entry point for the interactive search mode.

    Handles the complete workflow of gathering search parameters, executing the search,
    displaying results, and optionally exporting them to the selected format.
    """
    search_params = interactive_menu()
    start_time = time.time()

    # Use the common search execution function
    from .searcher import execute_search

    results = execute_search(search_params)

    # Display detailed interactive results
    display_results(results)

    # Export results if requested
    if search_params["export_format"] and results:
        exporter = ResultExporter(
            search_term=search_params["search_term"],
            directory=search_params["directory"],
        )
        output_path = exporter.export(results, search_params["export_format"])
        if output_path:
            print(f"\nResults exported to: {output_path}")

    elapsed_time = time.time() - start_time
    print(f"\nSearch completed in {elapsed_time:.2f} seconds.")


if __name__ == "__main__":
    interactive_main()
