"""Command line interface for the YAML diff tool."""

import argparse
import sys
from pathlib import Path

from .fetcher import YamlFetcher
from .comparer import YamlComparer


# Exit codes
EXIT_SUCCESS = 0
EXIT_KEYBOARD_INTERRUPT = 130
EXIT_ERROR = 1


def format_error_message(context: str, error: Exception) -> str:
    """Format error messages consistently across the CLI.

    Args:
        context: Description of what was being attempted
        error: The exception that occurred

    Returns:
        Formatted error message
    """
    return f"Failed to {context}: {error}"


def resolve_git_reference(commit: str = None, branch: str = None, default_branch: str = "main") -> str:
    """Resolve git reference, giving precedence to commit over branch.

    Args:
        commit: Commit hash if specified
        branch: Branch name if specified
        default_branch: Default branch to use if neither commit nor branch specified

    Returns:
        Git reference to use (commit takes precedence over branch)
    """
    if commit:
        return commit
    elif branch:
        return branch
    else:
        return default_branch


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        description="Compare Taqasta values.yml with Canasta recommended revisions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare main branch of Taqasta with main branch of Canasta
  python -m yaml_diff_tool

  # Compare specific branches
  python -m yaml_diff_tool --taqasta-branch develop --canasta-branch develop

  # Compare specific commits
  python -m yaml_diff_tool --taqasta-commit abc123 --canasta-commit def456

  # Save output to file
  python -m yaml_diff_tool --output diff.txt
        """
    )

    parser.add_argument(
        "--taqasta-branch",
        default="master",
        help="Branch of Taqasta repository to compare (default: master)"
    )

    parser.add_argument(
        "--canasta-branch",
        default="main",
        help="Branch of Canasta repository to compare (default: main)"
    )

    parser.add_argument(
        "--taqasta-commit",
        help="Specific commit hash of Taqasta repository to compare"
    )

    parser.add_argument(
        "--canasta-commit",
        help="Specific commit hash of Canasta repository to compare"
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Output file to save the diff (default: stdout)"
    )

    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path.home() / ".cache" / "yaml_diff_tool",
        help="Directory to cache downloaded YAML files"
    )

    return parser


def main() -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    try:
        # Initialize fetcher with cache directory
        fetcher = YamlFetcher(cache_dir=args.cache_dir)

        # Determine which refs to use (commit takes precedence over branch)
        taqasta_ref = resolve_git_reference(args.taqasta_commit, args.taqasta_branch, "master")
        canasta_ref = resolve_git_reference(args.canasta_commit, args.canasta_branch, "main")

        # Fetch YAML files
        taqasta_yaml = fetcher.fetch_taqasta_values(taqasta_ref)
        canasta_yaml = fetcher.fetch_canasta_revisions(canasta_ref, taqasta_yaml)

        # Detect MediaWiki version for display
        mw_version = fetcher._detect_mediawiki_version(taqasta_yaml)

        # Compare and generate diff
        comparer = YamlComparer()
        diff_output = comparer.compare(taqasta_yaml, canasta_yaml, taqasta_ref, canasta_ref, mw_version)

        # Output the results
        if args.output:
            try:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(diff_output)
                print(f"Diff saved to {args.output}")
            except (OSError, PermissionError) as e:
                print(format_error_message(f"write to output file {args.output}", e), file=sys.stderr)
                return EXIT_ERROR
        else:
            print(diff_output)

        return EXIT_SUCCESS

    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return EXIT_KEYBOARD_INTERRUPT
    except Exception as e:
        print(format_error_message("compare YAML files", e), file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
