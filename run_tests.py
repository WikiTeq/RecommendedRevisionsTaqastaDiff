#!/usr/bin/env python3
"""Script to run tests with coverage."""

import argparse
import subprocess
import sys


def create_parser():
    """Create argument parser for test runner."""
    parser = argparse.ArgumentParser(
        description="Run the test suite with configurable options",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests with coverage (default)
  python run_tests.py

  # Run tests without coverage
  python run_tests.py --no-coverage

  # Generate only HTML coverage report
  python run_tests.py --html-only

  # Run with custom coverage threshold
  python run_tests.py --fail-under=90

  # Run specific test file
  python run_tests.py --test-path=tests/test_comparer.py

  # Run with verbose output
  python run_tests.py --verbose
        """,
    )

    parser.add_argument("--no-coverage", action="store_true", help="Run tests without coverage reporting")

    parser.add_argument(
        "--html-only", action="store_true", help="Generate only HTML coverage report (no terminal output)"
    )

    parser.add_argument(
        "--fail-under", type=int, default=95, help="Fail if coverage is below this percentage (default: 95)"
    )

    parser.add_argument("--test-path", default="tests/", help="Path to tests to run (default: tests/)")

    parser.add_argument("--verbose", "-v", action="store_true", help="Run tests with verbose output")

    return parser


def run_tests(coverage=True, html_only=False, fail_under=95, test_path="tests/", verbose=False):
    """Run the test suite with configurable options.

    Args:
        coverage: Whether to run with coverage
        html_only: Whether to generate only HTML coverage report
        fail_under: Minimum coverage percentage to pass
        test_path: Path to tests to run
        verbose: Whether to run with verbose output

    Returns:
        Exit code from pytest
    """
    cmd = [sys.executable, "-m", "pytest"]

    if coverage:
        cmd.extend(["--cov=src"])

        if html_only:
            cmd.extend(["--cov-report=html"])
        else:
            cmd.extend(["--cov-report=html", "--cov-report=term-missing"])

        cmd.extend([f"--cov-fail-under={fail_under}"])

    if verbose:
        cmd.append("--verbose")

    cmd.append(test_path)

    result = subprocess.run(cmd, cwd=".")
    return result.returncode


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    coverage = not args.no_coverage
    html_only = args.html_only
    fail_under = args.fail_under
    test_path = args.test_path
    verbose = args.verbose

    return run_tests(
        coverage=coverage, html_only=html_only, fail_under=fail_under, test_path=test_path, verbose=verbose
    )


if __name__ == "__main__":
    sys.exit(main())
