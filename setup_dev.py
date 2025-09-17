#!/usr/bin/env python3
"""Development environment setup script."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"🔧 {description}...")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {' '.join(cmd)}")
        print(f"   Error: {e.stderr}")
        return False


def main():
    """Set up the development environment."""
    print("🚀 Setting up YAML Diff Tool development environment\n")

    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Error: pyproject.toml not found. Please run this script from the project root.")
        sys.exit(1)

    success = True

    # Install development dependencies
    if not run_command([sys.executable, "-m", "pip", "install", "-e", ".[dev]"], "Installing development dependencies"):
        success = False

    # Install pre-commit hooks
    if not run_command([sys.executable, "-m", "pre_commit", "install"], "Installing pre-commit hooks"):
        success = False

    # Run initial pre-commit checks
    if not run_command(
        [sys.executable, "-m", "pre_commit", "run", "--all-files"], "Running initial code quality checks"
    ):
        success = False

    if success:
        print("\n🎉 Development environment setup completed successfully!")
        print("\n📝 Next steps:")
        print("   - Make your changes")
        print("   - Run 'git add' and 'git commit' (hooks will run automatically)")
        print("   - Push your changes")
        print("\n🔍 Useful commands:")
        print("   python run_tests.py          # Run tests")
        print("   pre-commit run --all-files  # Manual quality check")
        print("   mypy src/                   # Type checking")
        print("   flake8 src/                 # Linting")
    else:
        print("\n❌ Development environment setup failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
