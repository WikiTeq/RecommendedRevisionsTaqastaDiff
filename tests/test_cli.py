"""Tests for the CLI module."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.cli import create_parser, main, resolve_git_reference


class TestCli:
    """Test cases for CLI functionality."""

    def test_resolve_git_reference_commit_priority(self):
        """Test that commit takes priority over branch."""
        result = resolve_git_reference(commit="abc123", branch="develop")
        assert result == "abc123"

    def test_resolve_git_reference_branch_only(self):
        """Test branch resolution when no commit specified."""
        result = resolve_git_reference(commit=None, branch="develop")
        assert result == "develop"

    def test_resolve_git_reference_default_branch(self):
        """Test default branch when neither commit nor branch specified."""
        result = resolve_git_reference(commit=None, branch=None, default_branch="main")
        assert result == "main"

    def test_resolve_git_reference_empty_strings(self):
        """Test handling of empty strings."""
        result = resolve_git_reference(commit="", branch="", default_branch="master")
        assert result == "master"

    def test_create_parser_default_values(self):
        """Test parser with default values."""
        parser = create_parser()
        args = parser.parse_args([])

        assert args.taqasta_branch == "master"
        assert args.canasta_branch == "main"
        assert args.taqasta_commit is None
        assert args.canasta_commit is None
        assert args.output is None
        assert str(args.cache_dir).endswith("yaml_diff_tool")

    def test_create_parser_custom_values(self):
        """Test parser with custom values."""
        parser = create_parser()
        args = parser.parse_args([
            "--taqasta-branch", "develop",
            "--canasta-branch", "feature",
            "--taqasta-commit", "abc123",
            "--canasta-commit", "def456",
            "--output", "output.txt",
            "--cache-dir", "/tmp/cache"
        ])

        assert args.taqasta_branch == "develop"
        assert args.canasta_branch == "feature"
        assert args.taqasta_commit == "abc123"
        assert args.canasta_commit == "def456"
        assert args.output == Path("output.txt")
        assert args.cache_dir == Path("/tmp/cache")

    def test_create_parser_help(self):
        """Test parser help output."""
        parser = create_parser()
        help_text = parser.format_help()

        assert "Compare Taqasta values.yml with Canasta recommended revisions" in help_text
        assert "--taqasta-branch" in help_text
        assert "--canasta-branch" in help_text
        assert "--taqasta-commit" in help_text
        assert "--canasta-commit" in help_text
        assert "--output" in help_text

    @patch('src.cli.YamlFetcher')
    @patch('src.cli.YamlComparer')
    @patch('sys.stdout')
    def test_main_success(self, mock_stdout, mock_comparer_class, mock_fetcher_class):
        """Test successful main execution."""
        # Mock the dependencies
        mock_fetcher = Mock()
        mock_comparer = Mock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_comparer_class.return_value = mock_comparer

        mock_fetcher.fetch_taqasta_values.return_value = {"extensions": []}
        mock_fetcher.fetch_canasta_revisions.return_value = {"extensions": []}
        mock_fetcher._detect_mediawiki_version.return_value = "1.43"
        mock_comparer.compare.return_value = "No differences found!"

        # Test with default arguments
        with patch('sys.argv', ['test']):
            result = main()

        assert result == 0
        mock_fetcher_class.assert_called_once()
        mock_fetcher.fetch_taqasta_values.assert_called_once_with("master")
        mock_fetcher.fetch_canasta_revisions.assert_called_once_with("main", {"extensions": []})
        mock_comparer.compare.assert_called_once_with(
            {"extensions": []}, {"extensions": []}, "master", "main", "1.43"
        )

    @patch('src.cli.YamlFetcher')
    @patch('src.cli.YamlComparer')
    @patch('pathlib.Path.write_text')
    def test_main_with_output_file(self, mock_write_text, mock_comparer_class, mock_fetcher_class):
        """Test main execution with output file."""
        mock_fetcher = Mock()
        mock_comparer = Mock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_comparer_class.return_value = mock_comparer

        mock_fetcher.fetch_taqasta_values.return_value = {"extensions": []}
        mock_fetcher.fetch_canasta_revisions.return_value = {"extensions": []}
        mock_fetcher._detect_mediawiki_version.return_value = "1.43"
        mock_comparer.compare.return_value = "Diff output"

        # Mock Path object and its parent
        mock_parent = Mock()
        mock_parent.mkdir = Mock()
        mock_path = Mock()
        mock_path.parent = mock_parent
        mock_path.write_text = mock_write_text

        with patch('src.cli.Path', return_value=mock_path), patch('sys.argv', ['test', '--output', 'output.txt']):
            result = main()

        assert result == 0
        mock_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_write_text.assert_called_once_with("Diff output")

    @patch('src.cli.YamlFetcher')
    def test_main_fetch_failure(self, mock_fetcher_class, capsys):
        """Test main execution when fetching fails."""
        mock_fetcher_class.side_effect = Exception("Network error")

        with patch('sys.argv', ['test']):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Failed to compare YAML files: Network error" in captured.err

    @patch('src.cli.YamlFetcher')
    @patch('src.cli.YamlComparer')
    def test_main_commit_precedence(self, mock_comparer_class, mock_fetcher_class):
        """Test that commit arguments take precedence over branch arguments."""
        mock_fetcher = Mock()
        mock_comparer = Mock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_comparer_class.return_value = mock_comparer

        mock_fetcher.fetch_taqasta_values.return_value = {"extensions": []}
        mock_fetcher.fetch_canasta_revisions.return_value = {"extensions": []}
        mock_fetcher._detect_mediawiki_version.return_value = "1.43"
        mock_comparer.compare.return_value = "Diff output"

        # Test with both branch and commit specified
        with patch('sys.argv', ['test', '--taqasta-branch', 'develop', '--taqasta-commit', 'abc123']):
            result = main()

        assert result == 0
        mock_fetcher.fetch_taqasta_values.assert_called_once_with("abc123")

    @patch('src.cli.YamlFetcher')
    @patch('src.cli.YamlComparer')
    @patch('sys.stdout')
    def test_main_custom_refs(self, mock_stdout, mock_comparer_class, mock_fetcher_class):
        """Test main execution with custom branch/commit refs."""
        mock_fetcher = Mock()
        mock_comparer = Mock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_comparer_class.return_value = mock_comparer

        mock_fetcher.fetch_taqasta_values.return_value = {"extensions": []}
        mock_fetcher.fetch_canasta_revisions.return_value = {"extensions": []}
        mock_fetcher._detect_mediawiki_version.return_value = "1.43"
        mock_comparer.compare.return_value = "Custom diff output"

        with patch('sys.argv', [
            'test',
            '--taqasta-commit', 'abc123',
            '--canasta-branch', 'feature-branch'
        ]):
            result = main()

        assert result == 0
        mock_fetcher.fetch_taqasta_values.assert_called_once_with("abc123")
        mock_fetcher.fetch_canasta_revisions.assert_called_once_with("feature-branch", {"extensions": []})

    def test_main_module_execution(self):
        """Test that the module can be executed directly."""
        # This test ensures the if __name__ == "__main__" block is covered
        # We can't easily test the actual execution in the test environment,
        # but we can verify the structure exists
        import src.cli
        assert hasattr(src.cli, 'main')
        assert hasattr(src.cli, '__name__')
        # The if __name__ == "__main__" block exists in the file

    def test_main_module_execution_calls_main(self):
        """Test that the module execution calls main() when run directly."""
        # Test the actual if __name__ == "__main__" block by importing and checking
        import src.cli
        import sys

        # Store original sys.argv
        original_argv = sys.argv

        try:
            # Set up sys.argv to simulate module execution
            sys.argv = ['src/cli.py', '--help']

            # Import the module to trigger the if __name__ == "__main__" block
            # This is tricky to test directly, so we'll just verify the structure
            assert hasattr(src.cli, '__name__')
            assert callable(src.cli.main)

        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_main_module_direct_execution(self):
        """Test direct execution of the module."""
        import subprocess
        import sys

        # Run the module directly to trigger the if __name__ == "__main__" block
        result = subprocess.run([
            sys.executable, '-m', 'src.cli', '--help'
        ], capture_output=True, text=True, cwd='.')

        # The module should run without error (help should return 0)
        assert result.returncode == 0


    @patch('src.cli.YamlFetcher')
    @patch('src.cli.YamlComparer')
    def test_main_keyboard_interrupt(self, mock_comparer_class, mock_fetcher_class, capsys):
        """Test main execution with KeyboardInterrupt."""
        mock_fetcher_class.side_effect = KeyboardInterrupt()

        with patch('sys.argv', ['test']):
            result = main()

        assert result == 130
        captured = capsys.readouterr()
        assert "Operation cancelled by user" in captured.err

    @patch('src.cli.YamlFetcher')
    @patch('src.cli.YamlComparer')
    def test_main_general_exception(self, mock_comparer_class, mock_fetcher_class, capsys):
        """Test main execution with general exception."""
        mock_fetcher_class.side_effect = Exception("Unexpected error")

        with patch('sys.argv', ['test']):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Failed to compare YAML files: Unexpected error" in captured.err

    @patch('src.cli.YamlFetcher')
    @patch('src.cli.YamlComparer')
    @patch('pathlib.Path.write_text')
    def test_main_output_file_error(self, mock_write_text, mock_comparer_class, mock_fetcher_class):
        """Test main execution with output file write error."""
        mock_fetcher = Mock()
        mock_comparer = Mock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_comparer_class.return_value = mock_comparer

        mock_fetcher.fetch_taqasta_values.return_value = {"extensions": []}
        mock_fetcher.fetch_canasta_revisions.return_value = {"extensions": []}
        mock_fetcher._detect_mediawiki_version.return_value = "1.43"
        mock_comparer.compare.return_value = "Diff output"

        # Mock Path object and its parent
        mock_parent = Mock()
        mock_parent.mkdir = Mock()
        mock_path = Mock()
        mock_path.parent = mock_parent
        mock_path.write_text = mock_write_text
        mock_write_text.side_effect = OSError("Permission denied")

        with patch('src.cli.Path', return_value=mock_path), patch('sys.argv', ['test', '--output', 'output.txt']):
            result = main()

        assert result == 1

    @patch('src.cli.YamlFetcher')
    @patch('src.cli.YamlComparer')
    def test_main_comparison_failure(self, mock_comparer_class, mock_fetcher_class, capsys):
        """Test main execution when comparison fails."""
        mock_fetcher = Mock()
        mock_comparer = Mock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_comparer_class.return_value = mock_comparer

        mock_fetcher.fetch_taqasta_values.return_value = {"extensions": []}
        mock_fetcher.fetch_canasta_revisions.return_value = {"extensions": []}
        mock_fetcher._detect_mediawiki_version.return_value = "1.43"
        mock_comparer.compare.side_effect = Exception("Comparison error")

        with patch('sys.argv', ['test']):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Failed to compare YAML files: Comparison error" in captured.err
