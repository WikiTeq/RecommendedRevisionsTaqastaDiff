# RecommendedRevisionsTaqastaDiff

![Banner](mascot.png)

A comprehensive tool to compare Taqasta's `values.yml` with Canasta's recommended revisions YAML files. This tool helps identify differences in extensions, skins, composer packages, and repositories between the two MediaWiki distributions, making it easier to maintain compatibility and track changes.

## Installation

### Option 1: Install from Source (Recommended)

```bash
git clone https://github.com/WikiTeq/RecommendedRevisionsTaqastaDiff.git
cd RecommendedRevisionsTaqastaDiff
pip install -e .
```

### Option 2: Install with Development Dependencies

For development, testing, and code quality tools:

```bash
pip install -e ".[dev]"
```

### Option 3: Install Dependencies Only

To install only runtime dependencies (for CI/CD or container environments):

```bash
pip install .
```

## Usage

### Basic Usage

Compare Taqasta master branch with Canasta main branch (default):

```bash
yaml-diff-tool
```

### Advanced Usage

Compare specific branches:

```bash
yaml-diff-tool --taqasta-branch develop --canasta-branch develop
```

Compare specific commits:

```bash
yaml-diff-tool --taqasta-commit abc123 --canasta-commit def456
```

Save output to file:

```bash
yaml-diff-tool --output diff.txt
```

Use custom cache directory:

```bash
yaml-diff-tool --cache-dir /path/to/cache
```

### Command Line Options

- `--taqasta-branch BRANCH`: Branch of Taqasta repository to compare (default: master)
- `--canasta-branch BRANCH`: Branch of Canasta repository to compare (default: main)
- `--taqasta-commit COMMIT`: Specific commit hash of Taqasta repository
- `--canasta-commit COMMIT`: Specific commit hash of Canasta repository
- `--output FILE`: Output file to save the diff (default: stdout)
- `--cache-dir DIR`: Directory to cache downloaded YAML files (default: ~/.cache/yaml_diff_tool)
- `--help`: Show help message

## Features

- **GitHub Integration**: Fetches YAML files directly from GitHub repositories with intelligent caching
- **Comprehensive Comparison**: Analyzes extensions, skins, composer packages, and custom repositories
- **Detailed Diff Output**: Shows differences in commits, repositories, branches, and additional steps
- **Flexible CLI**: Support for branches, commits, output files, and custom cache directories
- **Error Handling**: Robust error handling for network issues, invalid inputs, and file system errors
- **High Performance**: Efficient caching reduces repeated GitHub requests
- **Well Tested**: 97% test coverage with 71 comprehensive tests

## Output Format

The tool generates detailed comparison reports with the following structure:

### Header
- Shows the comparison being performed (Taqasta ref vs Canasta ref)
- Displays detected MediaWiki version (when available)

### Extensions Section
- **Extensions only in Taqasta/Canasta**: Lists extensions that exist in one repository but not the other
  - Shows commit hash and repository URL for context
- **Extensions with different configurations**: Shows extensions that exist in both but have differences in:
  - Commit hashes (most common difference)
  - Repository URLs (with normalization for .git suffixes)
  - Branch names (defaults to REL1_43 if not specified)
  - Additional steps (composer updates, database updates, etc.)

### Skins Section
- **Skins only in Taqasta/Canasta**: Lists skins unique to each repository
- **Skins with different configurations**: Shows differences in commit hashes

### Composer Packages Section
- **Composer packages only in Taqasta**: Lists packages that require composer updates in Taqasta
- **Extensions requiring composer update only in Canasta**: Lists extensions in Canasta that need composer updates

### Repositories Section
- **Custom repositories only in Taqasta/Canasta**: Lists repository URLs that are referenced in one distribution but not the other

### Summary
- Shows "No differences found!" when configurations are identical

## Example Output

```
Comparing Taqasta (master) vs Canasta (main)
MediaWiki Version: 1.43
======================================================================

EXTENSIONS:
  Extensions only in Taqasta:
    + AddMessages
        commit: a0af32f229d93016f3c3e80bcf2065e09f498064
        repository: https://github.com/wikimedia/mediawiki-extensions-AddMessages
    + Auth_remoteuser
        commit: c985d520c7aea38092ee7208be31f07a7251210d
        repository: https://github.com/wikimedia/mediawiki-extensions-Auth_remoteuser

  Extensions only in Canasta:
    - ExampleExtension
        commit: d4e5f6789abc0123456789abcdef0123456789abc

  Extensions with different configurations:
    ~ AWS:
        Taqasta commit: 97c210475f82ed5bc86ea3cbf2726162ccbedbfe
        Canasta commit: f85bb579b57f22175ff0cbca7664ad26cacdbb58
        Taqasta repo: https://github.com/edwardspec/mediawiki-aws-s3
        Canasta repo: https://github.com/edwardspec/mediawiki-aws-s3
    ~ VisualEditor:
        Taqasta commit: abc123def4567890123456789abcdef01234567
        Canasta commit: def4567890123456789abcdef0123456789abc
        Only in Taqasta: composer update

SKINS:
  Skins only in Taqasta:
    + CustomSkin
        commit: 1234567890abcdef1234567890abcdef12345678

COMPOSER PACKAGES:
  Composer packages only in Taqasta:
    + mediawiki/some-package @ dev

REPOSITORIES:
  Custom repositories only in Taqasta:
    + https://github.com/example/custom-repo
```

### Project Structure

```
RecommendedRevisionsTaqastaDiff/
├── src/
│   ├── __init__.py
│   ├── cli.py          # Command-line interface
│   ├── comparer.py     # YAML comparison logic
│   └── fetcher.py      # GitHub data fetching
├── tests/
│   ├── __init__.py
│   ├── test_cli.py     # CLI tests
│   ├── test_comparer.py # Comparison tests
│   └── test_fetcher.py # Fetcher tests
├── pyproject.toml      # Package configuration and dependencies
├── pytest.ini          # Pytest configuration
├── run_tests.py        # Test runner script with coverage
├── setup_dev.py        # Development environment setup
├── .gitignore          # Git ignore rules
├── mascot.png          # Banner image
└── README.md           # This file
```

## Development

### Code Quality Tools

This project uses several tools to maintain high code quality:

- **[Black](https://black.readthedocs.io/)** - Code formatter (PEP 8 compliant)
- **[flake8](https://flake8.pycqa.org/)** - Linting and style checking
- **[mypy](https://mypy-lang.org/)** - Static type checking
- **[isort](https://pycqa.github.io/isort/)** - Import sorting
- **[pre-commit](https://pre-commit.com/)** - Git hook management

### Setting up Development Environment

#### Quick Setup (Recommended)

Use the automated setup script:

```bash
python setup_dev.py
```

This will:
- Create a virtual environment
- Install all development dependencies
- Install pre-commit hooks
- Run initial quality checks

#### Manual Setup

1. Clone and enter the repository:
   ```bash
   git clone https://github.com/WikiTeq/RecommendedRevisionsTaqastaDiff.git
   cd RecommendedRevisionsTaqastaDiff
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

5. Run initial quality checks:
   ```bash
   pre-commit run --all-files
   ```

### Quality Gates

The following checks run automatically on commits:

- **Code formatting** with Black
- **Import sorting** with isort
- **Linting** with flake8
- **Type checking** with mypy
- **Tests** with pytest (97% coverage minimum)

### Manual Quality Checks

```bash
# Run tests with coverage
python run_tests.py

# Type checking
mypy src/

# Linting
flake8 src/

# Code formatting
black src/
isort src/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Troubleshooting

### Common Issues

**Network/Connection Errors**
- **Issue**: "Failed to fetch" or timeout errors
- **Solution**: Check your internet connection and try again. The tool will retry automatically for transient failures.

**Cache Issues**
- **Issue**: Outdated cached data
- **Solution**: Clear the cache directory (`~/.cache/yaml_diff_tool`) or use `--cache-dir` with a different path

**Permission Errors**
- **Issue**: Cannot write to cache directory or output file
- **Solution**: Ensure you have write permissions to the specified directories

**Installation Issues**
- **Issue**: Import errors or missing dependencies
- **Solution**: Ensure you're using the correct Python version (3.8+) and have installed dependencies with `pip install -e .`

**Git Reference Errors**
- **Issue**: "Branch/commit not found" errors
- **Solution**: Verify the branch/commit exists in the respective repositories (WikiTeq/Taqasta and CanastaWiki/RecommendedRevisions)

### Getting Help

- Check existing GitHub issues for similar problems
- Run `yaml-diff-tool --help` for usage information
- View test files for additional usage examples
- Enable verbose output by checking the test suite

## License

This project is part of the WikiTeq organization. Please refer to the WikiTeq organization licensing policies or contact the maintainers for licensing information.

For more information about licensing, check with the WikiTeq organization or create an issue in this repository.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the test files for usage examples
- Review the CLI help: `yaml-diff-tool --help`
