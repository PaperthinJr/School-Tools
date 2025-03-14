import sys
from pathlib import Path
from typing import Optional
import PySimpleGUI as sg
from document_search.interactive import interactive_main


def get_exe_directory() -> Optional[Path]:
    """
    Returns the directory where the .exe is located, or None if running as a Python script.
    """
    return Path(sys.executable).parent.resolve() if getattr(sys, "frozen", False) else None


def select_directory_gui(default_directory: Path) -> Optional[Path]:
    """
    Opens a GUI dialog for selecting a directory.

    Args:
        default_directory (Path): The default directory (usually the .exe directory).

    Returns:
        Path: The directory selected by the user, or None if the user cancels.
    """
    sg.theme("DarkBlue")  # Set a theme for the GUI

    layout = [
        [sg.Text("Select a folder to search or press OK to use the detected directory:")],
        [sg.Input(default_text=str(default_directory), key="-FOLDER-", size=(50, 1)), sg.FolderBrowse()],
        [sg.Button("OK"), sg.Button("Cancel")]
    ]

    window = sg.Window("Document Search - Select Directory", layout)
    event, values = window.read()
    window.close()

    if event == "Cancel" or event == sg.WIN_CLOSED:
        return None  # Return None if user cancels or closes the window

    return Path(values["-FOLDER-"]).resolve()


def exe_main():
    """
    Custom entry point for the standalone .exe version.

    - Uses a GUI for folder selection.
    - Runs the interactive search.
    - Ensures exports save in the .exe directory.
    """
    exe_directory = get_exe_directory()
    search_directory = select_directory_gui(exe_directory if exe_directory else Path.cwd())
    if search_directory is None:
        print("❌ Directory selection was cancelled. Exiting.")
        return

    print(f"✅ Search will be performed in: {search_directory}")

    # Pass the directory to interactive_main
    sys.argv = ["exe.py", "--directory", str(search_directory)]
    interactive_main()