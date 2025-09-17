"""Command line interface for the YAML diff tool."""

import argparse
import sys
from pathlib import Path

from .fetcher import YamlFetcher
from .comparer import YamlComparer


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
        taqasta_ref = args.taqasta_commit or args.taqasta_branch
        canasta_ref = args.canasta_commit or args.canasta_branch

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
                print(f"Error writing to output file {args.output}: {e}", file=sys.stderr)
                return 1
        else:
            print(diff_output)

        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
