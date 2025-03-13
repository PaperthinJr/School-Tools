# Document Search

A comprehensive Python tool for searching text patterns across multiple document types with advanced filtering, context capturing, and result exporting capabilities.

## Features

- **Multi-format Support**: Search across text files, PDFs, Word documents, and more
- **Advanced Search Patterns**: Support for regex, case sensitivity, and word boundary options
- **Context Capture**: View search results with surrounding text for better context
- **Result Exporting**: Export findings to various formats (CSV, JSON, HTML)
- **CLI & Interactive Modes**: Both command-line and interactive interfaces available
- **Performance Optimized**: Efficient processing for large document collections

## Installation

```bash
# Install from PyPI
pip install document-search

# Or install from source
git clone https://github.com/username/document-search.git
cd document-search
pip install -e .
```

## Requirements

- Python 3.7+
- Required dependencies are listed in `requirements.txt`

## Usage

### Command Line Interface

Search for a pattern in documents:

```bash
# Basic search
document-search --pattern "example" --directory ./documents

# Search with regex
document-search --pattern "data\s+analysis" --regex --directory ./documents

# Case-sensitive search with context
document-search --pattern "API" --case-sensitive --context 2 --directory ./documents
```

### Python API

```python
from document_search import execute_search, WordSearcher, ResultExporter

# Create a searcher
searcher = WordSearcher(
    pattern="example",
    case_sensitive=False,
    regex_mode=False,
    whole_words=True
)

# Execute search
results = execute_search(
    searcher=searcher,
    directory="./documents",
    file_types=[".txt", ".pdf", ".docx"],
    context_lines=2
)

# Export results
exporter = ResultExporter(results)
exporter.to_csv("search_results.csv")
exporter.to_json("search_results.json")
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--pattern` | Text pattern to search for |
| `--directory` | Directory to search in |
| `--regex` | Enable regex pattern matching |
| `--case-sensitive` | Make search case-sensitive |
| `--whole-words` | Match only whole words |
| `--context` | Number of context lines to include |
| `--file-types` | Comma-separated list of file extensions to include |
| `--exclude` | Patterns to exclude from search |
| `--output` | Output file for results |
| `--format` | Output format (csv, json, html) |
| `--interactive` | Launch interactive search mode |

## Interactive Mode

Start the interactive search shell:

```bash
document-search --interactive
```

In interactive mode, you can:
- Set search patterns and options
- Navigate through results
- Filter and refine searches
- Export findings on-the-fly

## API Documentation

### Core Components

- `WordSearcher`: Main search engine class with pattern matching capabilities
- `execute_search`: Function to run searches across file collections
- `SearchMatch`: Data model for search matches with context
- `ResultExporter`: Utility to export findings to various formats

### Search Configuration

```python
from document_search import WordSearcher

searcher = WordSearcher(
    pattern="example",        # Pattern to search for
    case_sensitive=False,     # Case sensitivity
    regex_mode=False,         # Regular expression mode
    whole_words=True,         # Match whole words only
    match_highlighter=True    # Highlight matches in output
)
```

## Configuration

Create a `.document-search.yaml` in your project directory for default settings:

```yaml
default_directory: ./documents
file_types: [.txt, .md, .pdf, .docx]
excluded_patterns: [.git, .venv]
context_lines: 2
export_format: json
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Contributors and maintainers
- Python text processing community
- Open source document parsing libraries