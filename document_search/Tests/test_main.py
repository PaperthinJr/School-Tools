import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from document_search.main import main, run_search


class TestMain(unittest.TestCase):

    @patch("document_search.main.execute_search")
    def test_run_search(self, mock_execute_search):
        """Test that run_search calls execute_search with the provided parameters"""
        search_params = {
            "search_term": "test",
            "directory": Path("/test/path"),
            "case_sensitive": False,
        }

        run_search(search_params)

        mock_execute_search.assert_called_once_with(search_params)

    @patch("document_search.main.interactive_main")
    @patch("document_search.main.parse_arguments")
    def test_main_interactive_flag(self, mock_parse_arguments, mock_interactive_main):
        """Test main function calls interactive_main when interactive flag is set"""
        # Setup mock for args with interactive flag
        mock_args = MagicMock()
        mock_args.interactive = True
        mock_args.search_term = "test"
        mock_args.directory = "/test/path"
        mock_parse_arguments.return_value = mock_args

        main()

        mock_interactive_main.assert_called_once()

    @patch("document_search.main.interactive_main")
    @patch("document_search.main.parse_arguments")
    def test_main_missing_search_term(self, mock_parse_arguments, mock_interactive_main):
        """Test main function calls interactive_main when search term is missing"""
        # Setup mock for args with missing search term
        mock_args = MagicMock()
        mock_args.interactive = False
        mock_args.search_term = None
        mock_args.directory = "/test/path"
        mock_parse_arguments.return_value = mock_args

        main()

        mock_interactive_main.assert_called_once()

    @patch("document_search.main.interactive_main")
    @patch("document_search.main.parse_arguments")
    def test_main_missing_directory(self, mock_parse_arguments, mock_interactive_main):
        """Test main function calls interactive_main when directory is missing"""
        # Setup mock for args with missing directory
        mock_args = MagicMock()
        mock_args.interactive = False
        mock_args.search_term = "test"
        mock_args.directory = None
        mock_parse_arguments.return_value = mock_args

        main()

        mock_interactive_main.assert_called_once()

    @patch("document_search.main.run_search")
    @patch("document_search.main.get_search_params")
    @patch("document_search.main.parse_arguments")
    def test_main_cli_mode(self, mock_parse_arguments, mock_get_search_params, mock_run_search):
        """Test main function runs in CLI mode when search term and directory are provided"""
        # Setup mock for complete args
        mock_args = MagicMock()
        mock_args.interactive = False
        mock_args.search_term = "test"
        mock_args.directory = "/test/path"
        mock_parse_arguments.return_value = mock_args

        # Setup mock search params
        search_params = {"search_term": "test", "directory": Path("/test/path")}
        mock_get_search_params.return_value = search_params

        main()

        mock_get_search_params.assert_called_once_with(mock_args)
        mock_run_search.assert_called_once_with(search_params)
