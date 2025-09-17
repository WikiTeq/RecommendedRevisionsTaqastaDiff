#!/usr/bin/env python3
"""Script to run tests with coverage."""

import subprocess
import sys


def run_tests():
    """Run the test suite with coverage."""
    cmd = [
        sys.executable, "-m", "pytest",
        "--cov=src",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-fail-under=100",
        "tests/"
    ]

    result = subprocess.run(cmd, cwd=".")
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests())
