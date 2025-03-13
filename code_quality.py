"""
CODE QUALITY MANAGEMENT FOR PYTHON PROJECTS

This module provides a comprehensive suite of code quality tools for Python projects,
integrating popular utilities into a single, configurable workflow.

Tools included:
- Ruff: Fast Python linter and code formatter for error_handling checking and import sorting
- Black: PEP 8 compliant code formatter that provides consistent style
- Mypy: Static type checker to identify type-related error_handling
- Bandit: Security analyzer to find common security issues

Features:
- Auto-detects project configuration from pyproject.toml, requirements.txt, or environment.yml
- Adapts tool behavior based on existing configurations
- Runs checks in parallel for improved performance
- Provides both CLI usage and importable API
- CI-friendly with environment detection and machine-readable output

Command-line options:
    --check       Verify formatting without making changes
    --diff        Show changes Black would make without applying them
    --verbose     Display detailed output from tools
    --black-only  Skip other checks and run only Black formatter
    --ci-output   Generate JSON output for CI systems

Exit codes:
    0: All checks passed successfully
    1: One or more checks failed or would make changes in check mode
    2: Missing required tool dependencies
    Other: Tool-specific error_handling occurred

Usage examples:
    # Run all checks and apply formatting
    $ python code_quality.py

    # Check formatting without modifying files
    $ python code_quality.py --check

    # Run only Black formatter with detailed output
    $ python code_quality.py --black-only --verbose

    # Generate JSON output for CI systems
    $ python code_quality.py --ci-output

CI Integration (GitHub Actions):
    name: Code Quality Checks

    on: [push, pull_request]

    jobs:
      quality:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v3
          - name: Set up Python
            uses: actions/setup-python@v4
            with:
              python-version: '3.11'
          - name: Install dependencies
            run: |
              pip install toml pyyaml ruff black mypy bandit
          - name: Run code quality checks
            run: python core/utils/code_quality.py --check --ci-output

Library usage:
    from core.utils.code_quality import run_ruff, run_black, run_parallel_checks

    # Run individual tools
    run_ruff()
    run_black(check_only_mode=True)

    # Run multiple checks in parallel
    run_parallel_checks()
"""

# Author: Randy Wilson
# GitHub: PaperthinJr
# Date: 03/05/2025

import concurrent.futures
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, TypedDict

# =================================
# TOOL CONFIGURATION & DEFAULTS
# =================================

# Configuration for optional dependencies
# Set these flags to False if you want to disable a specific configuration source
USE_TOML_CONFIG: bool = False  # Controls pyproject.toml configuration parsing
USE_YAML_CONFIG: bool = False  # Controls environment.yml configuration parsing

# Type aliases for improved readability
CommandArguments = list[str]  # Command-line arguments for tools
ConfigurationDict = dict[str, Any]  # Configuration from project files
CommandResult = tuple[int, str]  # Exit code and output from command execution


class Environment(TypedDict):
    """Environment information for reporting and CI detection."""

    ci: bool  # Whether running in a CI environment
    python_version: str  # Current Python version


class Summary(TypedDict):
    """Overall summary of all check results."""

    success: bool  # True if all checks passed


class ToolResult(TypedDict, total=False):
    """Results from running an individual code quality tool."""

    success: bool  # Whether the tool executed successfully
    exit_code: int  # The tool's exit code
    check_mode: bool  # Whether the tool was run in check-only mode


class CheckResults(TypedDict):
    """Complete results from all code quality checks."""

    tools: dict[str, ToolResult]  # Results from individual tools
    timestamp: str  # When the checks were run
    environment: Environment  # Information about the runtime environment
    summary: Summary  # Overall success/failure status


# Get the current Python version formatted as expected by Black
PYTHON_VERSION: str = f"py{sys.version_info.major}{sys.version_info.minor}"

# Default arguments if no pyproject.toml is found
RUFF_DEFAULT_ARGS: CommandArguments = [
    "--select",
    "E,F,B,SIM,I,UP",  # Error, Flake8, Bug detection, Simplify, Imports, Upgrade
    "--fix",  # Automatically fix issues where possible
    "--ignore",
    "D300,Q000,Q001,Q002,Q003,COM812",  # Docstrings and quotes to ignore
    "--line-length",
    "100",  # Maximum line length
]

BLACK_DEFAULT_ARGS: CommandArguments = ["--line-length", "100", "--target-version", PYTHON_VERSION]

MYPY_ARGS: CommandArguments = ["--strict", "."]  # Most strict type checking

BANDIT_ARGS: CommandArguments = [
    "-r",
    ".",  # Recursive scan
    "-f",
    "json",  # Output format
    "-n",
    "3",  # Number of processes
    "--severity-level",
    "medium",  # Minimum issue severity to report
    "--confidence-level",
    "medium",  # Minimum issue confidence to report
    "--exclude",
    "*/tests/*,*/venv/*,*/.venv/*",  # Directories to exclude
]

# Required tools for the script to function
REQUIRED_TOOLS = ["ruff", "black", "mypy", "bandit"]

# =================================
# ENVIRONMENT DETECTION
# =================================


def is_ci_environment() -> bool:
    """Detect if the script is running in a CI environment.

    Checks for the presence of common CI environment variables from
    popular CI systems like GitHub Actions, GitLab CI, Travis, etc.

    Returns:
        bool: True if running in a CI environment, False otherwise
    """
    ci_variables = [
        "CI",  # Generic CI indicator
        "GITHUB_ACTIONS",  # GitHub Actions
        "GITLAB_CI",  # GitLab CI
        "TRAVIS",  # Travis CI
        "CIRCLECI",  # Circle CI
        "JENKINS_URL",  # Jenkins
        "TEAMCITY_VERSION",  # TeamCity
        "AZURE_PIPELINE_BUILD",  # Azure Pipelines
    ]

    return any(os.environ.get(var) for var in ci_variables)


# =================================
# UTILITY FUNCTIONS & HELPERS
# =================================


def validate_environment() -> bool:
    """Validate that all required tools are installed and available in PATH.

    Checks for the presence of each tool in REQUIRED_TOOLS and provides
    installation instructions if any are missing.

    Returns:
        bool: True if all tools are available, False otherwise
    """
    missing_tools = []

    for tool in REQUIRED_TOOLS:
        if not shutil.which(tool):
            missing_tools.append(tool)

    if missing_tools:
        tools_list = " ".join(missing_tools)
        logger.error(f"Missing required tools: {', '.join(missing_tools)}")
        logger.error("Please install them with one of these methods:")
        logger.error(f"  pip install {tools_list}")
        logger.error(f"  conda install -c defaults -c conda-forge {tools_list}")
        return False

    return True


def find_project_root() -> Path:
    """Find the project root by looking for specific files.

    The function traverses upward from the current directory, looking for
    common project indicator files like .git, pyproject.toml, etc.
    This helps ensure tools run from the correct base directory.

    Returns:
        Path: The path to the identified project root directory.
    """
    current_directory_path: Path = Path.cwd()
    project_indicator_files: set[str] = {
        ".git",
        ".gitignore",
        ".pre-commit-config.yaml",
        "pyproject.toml",
        "requirements.txt",
    }

    # Walk upwards until we find a marker file or hit the filesystem root
    while (
        not any(
            (current_directory_path / indicator_file).exists()
            for indicator_file in project_indicator_files
        )
        and current_directory_path != current_directory_path.parent
    ):
        current_directory_path = current_directory_path.parent

    return current_directory_path


# Setup logging for the module
project_root_path: Path = find_project_root()
log_filename: str = f"code_quality_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_filepath: Path = project_root_path / log_filename

# Configure logging based on environment - simplified format for CI systems
is_ci = is_ci_environment()
log_format = (
    "%(levelname)s: %(message)s"
    if is_ci
    else "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[logging.FileHandler(log_filepath), logging.StreamHandler(sys.stdout)],
)
logger: logging.Logger = logging.getLogger(__name__)


def read_project_config() -> ConfigurationDict:
    """Read and parse project configuration from available config files.

    Checks for and reads configuration from:
    - pyproject.toml (if USE_TOML_CONFIG is True)
    - requirements.txt
    - environment.yml (if USE_YAML_CONFIG is True)

    Returns:
        ConfigurationDict: Dictionary containing merged configuration from all sources
    """
    project_directory: Path = find_project_root()
    requirements_file_path: Path = project_directory / "requirements.txt"
    project_config: ConfigurationDict = {}

    # Read from pyproject.toml if it exists and is enabled
    if USE_TOML_CONFIG:
        pyproject_config_path: Path = project_directory / "pyproject.toml"
        if pyproject_config_path.exists():
            try:
                try:
                    import toml  # type: ignore
                except ImportError:
                    logger.warning("toml package not installed. Unable to read pyproject.toml.")
                else:
                    project_config = toml.load(pyproject_config_path)
            except Exception as toml_error:
                logger.warning(f"Failed to read pyproject.toml: {toml_error}")

    # Read from requirements.txt if it exists
    if requirements_file_path.exists():
        try:
            with open(requirements_file_path) as requirements_file:
                requirement_lines: list[str] = requirements_file.read().splitlines()
                project_config["dependencies"] = requirement_lines
        except Exception as requirements_error:
            logger.warning(f"Failed to read requirements.txt: {requirements_error}")

    # Read from environment.yml if it exists and is enabled
    if USE_YAML_CONFIG:
        environment_config_path: Path = project_directory / "environment.yml"
        if environment_config_path.exists():
            try:
                try:
                    import yaml  # type: ignore
                except ImportError:
                    logger.warning("pyyaml package not installed. Unable to read environment.yml.")
                else:
                    with open(environment_config_path) as environment_file:
                        environment_yaml: dict[str, Any] = yaml.safe_load(environment_file)
                        if "dependencies" in environment_yaml:
                            project_config["dependencies"] = environment_yaml["dependencies"]
            except Exception as yaml_error:
                logger.warning(f"Failed to read environment.yml: {yaml_error}")

    return project_config


def get_ruff_args(project_config: ConfigurationDict) -> CommandArguments:
    """Get Ruff arguments from project configuration or use defaults.

    Determines whether to use Ruff configuration from pyproject.toml or
    fall back to default arguments when no configuration exists.

    Args:
        project_config: Project configuration dictionary from pyproject.toml or other sources

    Returns:
        CommandArguments: List of command-line arguments for Ruff
    """
    ruff_command_args: CommandArguments = RUFF_DEFAULT_ARGS.copy()

    # If Ruff is configured in pyproject.toml, use minimal arguments and rely on that config
    if "tool" in project_config and "ruff" in project_config.get("tool", {}):
        # We'll use Ruff's own configuration from pyproject.toml
        # and only add the --fix argument
        return ["check", "--fix", "."]

    return ["check", "."] + ruff_command_args


def get_black_args(project_config: ConfigurationDict) -> CommandArguments:
    """Get Black arguments from project configuration or use defaults.

    Extracts Black configuration from pyproject.toml if available,
    or falls back to default arguments. Handles line-length, target-version,
    and other customizable Black options.

    Args:
        project_config: Project configuration dictionary from pyproject.toml

    Returns:
        CommandArguments: List of command-line arguments for Black
    """
    black_command_args: CommandArguments = BLACK_DEFAULT_ARGS.copy()

    if "tool" in project_config and "black" in project_config["tool"]:
        black_config_section: dict[str, Any] = project_config["tool"]["black"]

        # Handle line-length by filtering out existing settings
        if "line-length" in black_config_section:
            filtered_args = []
            skip_next = False
            for arg in black_command_args:
                if skip_next:
                    skip_next = False
                    continue
                if arg == "--line-length":
                    skip_next = True
                else:
                    filtered_args.append(arg)
            black_command_args = filtered_args
            black_command_args.extend(["--line-length", str(black_config_section["line-length"])])

        # Handle target-version by filtering out existing settings
        if "target-version" in black_config_section:
            filtered_args = []
            skip_next = False
            for arg in black_command_args:
                if skip_next:
                    skip_next = False
                    continue
                if arg == "--target-version":
                    skip_next = True
                else:
                    filtered_args.append(arg)
            black_command_args = filtered_args

            if isinstance(black_config_section["target-version"], list):
                for version_string in black_config_section["target-version"]:
                    black_command_args.extend(["--target-version", version_string])
            else:
                black_command_args.extend(
                    ["--target-version", black_config_section["target-version"]]
                )

        # Append additional flags
        if black_config_section.get("skip-string-normalization", False):
            black_command_args.append("--skip-string-normalization")
        if black_config_section.get("skip-magic-trailing-comma", False):
            black_command_args.append("--skip-magic-trailing-comma")
        if black_config_section.get("preview", False):
            black_command_args.append("--preview")

    return black_command_args


# =================================
# COMMAND EXECUTION & PROCESS HANDLING
# =================================


def run_command(
    command_parts: list[str], tool_name: str, success_exit_codes: Optional[list[int]] = None
) -> tuple[int, str]:
    """Execute a shell command and capture its output.

    Runs a subprocess with the given command parts, captures stdout and stderr,
    and returns the exit code and output.

    Args:
        command_parts: List of command parts to execute
        tool_name: Name of the tool being run (for logging)
        success_exit_codes: Exit codes that indicate success (default is [0])

    Returns:
        tuple[int, str]: A tuple containing (exit_code, command_output)
    """
    if success_exit_codes is None:
        success_exit_codes = [0]

    logger.info(f"Running {tool_name}: {' '.join(command_parts)}")

    process_result = subprocess.run(command_parts, capture_output=True, text=True, encoding="utf-8")

    command_output = process_result.stdout
    if process_result.stderr and (process_result.returncode not in success_exit_codes):
        command_output += f"\n{process_result.stderr}"

    return process_result.returncode, command_output


# =================================
# TOOL RUNNERS & QUALITY CHECKS
# =================================


def run_ruff() -> int:
    """Run Ruff for linting, fixing, and import sorting.

    Executes the Ruff linter with the appropriate arguments, handling configuration
    from project files if available. Accepts exit code 1 from Ruff as success
    since it indicates fixable issues were found and fixed.

    Returns:
        int: Exit code (0 for success, non-zero for error_handling)
    """
    logger.info("Running Ruff (Linting & Import Sorting)...")
    project_config: ConfigurationDict = read_project_config()
    ruff_command_args: CommandArguments = get_ruff_args(project_config)

    ruff_exit_code: int
    ruff_output: str
    ruff_exit_code, ruff_output = run_command(["ruff"] + ruff_command_args, "Ruff", [0, 1])
    logger.info(ruff_output)

    # Exit code 1 from Ruff means it found and fixed issues, not a failure
    return 0 if ruff_exit_code in [0, 1] else ruff_exit_code


def run_black(
    check_only_mode: bool = False, diff_mode: bool = False, verbose_mode: bool = False
) -> bool:
    """Run Black code formatter with specified options.

    Executes the Black code formatter with configuration from the project
    settings or defaults. Can run in check-only mode to verify formatting
    without making changes, or in diff mode to show proposed changes.

    Args:
        check_only_mode: Whether to check formatting without modifying files
        diff_mode: Whether to show changes that would be made
        verbose_mode: Whether to show detailed output

    Returns:
        bool: True if formatting is correct or was applied successfully,
              False if changes would be made in check mode or on error_handling
    """
    project_config: dict[str, Any] = read_project_config()
    black_command_args: list[str] = get_black_args(project_config)

    # Add mode-specific arguments
    if check_only_mode:
        black_command_args.append("--check")
    if diff_mode:
        black_command_args.append("--diff")
    if verbose_mode:
        black_command_args.append("--verbose")

    black_command: list[str] = ["black", "."] + black_command_args
    black_exit_code: int
    black_output: str
    black_exit_code, black_output = run_command(black_command, "Black (Code Formatting)", [0, 1])

    logger.info(black_output)

    if black_exit_code == 0:
        logger.info("Black: Code formatting is correct")
        return True
    elif black_exit_code == 1 and check_only_mode:
        logger.info("✗ Black: Some files would be reformatted")
        return False
    elif black_exit_code == 123:
        logger.info("✗ Black: Internal error_handling occurred")
        return False

    return black_exit_code == 0


def run_mypy() -> int:
    """Run Mypy for static type checking.

    Executes Mypy with strict type checking enabled for the current project.
    Uses the MYPY_ARGS configuration which typically includes --strict.

    Returns:
        int: Exit code (0 for success, non-zero for type error_handling)
    """
    logger.info("Running Mypy (Type Checking)...")
    mypy_exit_code: int
    mypy_output: str
    mypy_exit_code, mypy_output = run_command(["mypy"] + MYPY_ARGS, "Mypy")
    logger.info(mypy_output)
    return mypy_exit_code


def run_bandit() -> int:
    """Run Bandit for security analysis.

    Executes Bandit security scanner with medium severity/confidence thresholds.
    Scans recursively while excluding test and virtual environment directories.

    Returns:
        int: Exit code (0 for no security issues, non-zero for issues found)
    """
    logger.info("Running Bandit (Security Analysis)...")
    bandit_exit_code: int
    bandit_output: str
    bandit_exit_code, bandit_output = run_command(["bandit"] + BANDIT_ARGS, "Bandit")

    logger.info(bandit_output)
    return bandit_exit_code


def run_parallel_checks() -> None:
    """Run Mypy and Bandit checks concurrently.

    Executes type checking and security scanning in parallel threads
    to improve performance. If either check fails, exits the program
    with a non-zero exit code.
    """
    logger.info("Running Mypy & Bandit (Parallel Type & Security Checks)...")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit both tasks to the executor
        future_mypy: concurrent.futures.Future[int] = executor.submit(run_mypy)
        future_bandit: concurrent.futures.Future[int] = executor.submit(run_bandit)

        # Wait for both to complete and get their results
        mypy_exit_code: int = future_mypy.result()
        bandit_exit_code: int = future_bandit.result()

        # Exit if any check failed
        if mypy_exit_code != 0 or bandit_exit_code != 0:
            sys.exit(1)


# =================================
# CI INTEGRATION & JSON OUTPUT
# =================================


def generate_json_output(data: CheckResults) -> str:
    """Generate JSON output for CI consumption.

    Creates a structured JSON representation of all check results,
    suitable for parsing by CI systems or other automation tools.

    Args:
        data: Dictionary containing tool results and environment information

    Returns:
        str: JSON string representation of results with indentation for readability
    """
    return json.dumps(data, indent=2)


def run_all_checks(
    check_mode: bool, diff_mode: bool, verbose_mode: bool, ci_output: bool
) -> CheckResults:
    """Run all code quality checks and collect results.

    Executes all tools (Ruff, Black, Mypy, Bandit) in sequence or parallel
    as appropriate, and collects their results into a structured format.

    Args:
        check_mode: Whether to check formatting without modifying files
        diff_mode: Whether to show changes that would be made
        verbose_mode: Whether to show detailed output
        ci_output: Whether to generate JSON output for CI consumption

    Returns:
        CheckResults: Dictionary containing results of all checks and metadata
    """
    check_results: CheckResults = {
        "tools": {},
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "ci": is_ci,
            "python_version": PYTHON_VERSION,
        },
        "summary": {"success": True},
    }

    # Run Ruff
    ruff_exit_code = run_ruff()
    check_results["tools"]["ruff"] = {"success": ruff_exit_code == 0, "exit_code": ruff_exit_code}
    if ruff_exit_code != 0:
        check_results["summary"]["success"] = False

    # Run Black
    black_success = run_black(check_mode, diff_mode, verbose_mode)
    check_results["tools"]["black"] = {"success": black_success, "check_mode": check_mode}
    if not black_success and check_mode:
        check_results["summary"]["success"] = False

    # Run Mypy and Bandit in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_mypy = executor.submit(run_mypy)
        future_bandit = executor.submit(run_bandit)

        mypy_exit_code = future_mypy.result()
        bandit_exit_code = future_bandit.result()

        check_results["tools"]["mypy"] = {
            "success": mypy_exit_code == 0,
            "exit_code": mypy_exit_code,
        }
        check_results["tools"]["bandit"] = {
            "success": bandit_exit_code == 0,
            "exit_code": bandit_exit_code,
        }

        if mypy_exit_code != 0 or bandit_exit_code != 0:
            check_results["summary"]["success"] = False

    if ci_output:
        logger.info(f"CI Results:\n{generate_json_output(check_results)}")

    return check_results


# =================================
# COMMAND-LINE INTERFACE & PARSING
# =================================

if __name__ == "__main__":
    import argparse

    # Set up command-line argument parsing
    argument_parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Run code quality tools"
    )
    argument_parser.add_argument(
        "--check", action="store_true", help="Check code formatting without modifying files"
    )
    argument_parser.add_argument(
        "--diff", action="store_true", help="Show diff of changes Black would make"
    )
    argument_parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    argument_parser.add_argument("--black-only", action="store_true", help="Run only Black")
    argument_parser.add_argument(
        "--ci-output", action="store_true", help="Generate JSON output for CI systems"
    )

    parsed_arguments: argparse.Namespace = argument_parser.parse_args()

    # Check if we're in a CI environment
    if is_ci:
        logger.info("Running in CI environment")

    # Validate environment - make sure all tools are installed
    if not validate_environment():
        sys.exit(2)

    # Handle black-only mode
    if parsed_arguments.black_only:
        formatting_success: bool = run_black(
            parsed_arguments.check, parsed_arguments.diff, parsed_arguments.verbose
        )
        sys.exit(0 if formatting_success else 1)

    # Run full code quality check sequence
    if parsed_arguments.ci_output:
        results = run_all_checks(
            parsed_arguments.check, parsed_arguments.diff, parsed_arguments.verbose, True
        )
        sys.exit(0 if results["summary"]["success"] else 1)
    else:
        ruff_result: int = run_ruff()
        if ruff_result != 0:
            sys.exit(ruff_result)

        black_formatting_success: bool = run_black(
            parsed_arguments.check, parsed_arguments.diff, parsed_arguments.verbose
        )
        if not black_formatting_success and parsed_arguments.check:
            sys.exit(1)

        run_parallel_checks()
