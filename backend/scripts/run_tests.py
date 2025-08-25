#!/usr/bin/env python3
"""
Script to run tests for the Learnobot application.
"""

import os
import sys
import subprocess
import argparse


def run_command(command, description):
    """Run a command and return success status."""
    print(f"🔄 {description}...")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ {description} completed successfully")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(e.stdout)
        print(e.stderr)
        return False, e.stderr


def run_pytest(test_path=None, coverage=False, verbose=False):
    """Run pytest with optional parameters."""
    
    command_parts = ["python", "-m", "pytest"]
    
    if test_path:
        command_parts.append(test_path)
    else:
        command_parts.append("tests/")
    
    if coverage:
        command_parts.extend([
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])
    
    if verbose:
        command_parts.append("-v")
    
    command_parts.extend([
        "--tb=short",
        "-x"  # Stop on first failure
    ])
    
    command = " ".join(command_parts)
    return run_command(command, "Running tests")


def run_linting():
    """Run code linting checks."""
    success = True
    
    # Run flake8
    flake8_success, _ = run_command(
        "python -m flake8 app/ tests/ --max-line-length=100 --ignore=E203,W503",
        "Running flake8 linting"
    )
    
    if not flake8_success:
        success = False
    
    # Run black check
    black_success, _ = run_command(
        "python -m black --check app/ tests/",
        "Checking code formatting with black"
    )
    
    if not black_success:
        print("💡 Run 'python -m black app/ tests/' to fix formatting")
        success = False
    
    return success


def run_type_checking():
    """Run type checking with mypy."""
    return run_command(
        "python -m mypy app/ --ignore-missing-imports",
        "Running type checking with mypy"
    )


def install_test_dependencies():
    """Install test dependencies."""
    dependencies = [
        "pytest",
        "pytest-asyncio", 
        "pytest-cov",
        "flake8",
        "black",
        "mypy"
    ]
    
    for dep in dependencies:
        success, _ = run_command(
            f"pip install {dep}",
            f"Installing {dep}"
        )
        if not success:
            return False
    
    return True


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run Learnobot tests")
    parser.add_argument(
        "--test-path", 
        help="Specific test file or directory to run"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true",
        help="Run tests with coverage reporting"
    )
    parser.add_argument(
        "--lint", 
        action="store_true",
        help="Run linting checks"
    )
    parser.add_argument(
        "--type-check", 
        action="store_true",
        help="Run type checking"
    )
    parser.add_argument(
        "--install-deps", 
        action="store_true",
        help="Install test dependencies"
    )
    parser.add_argument(
        "--all", 
        action="store_true",
        help="Run all checks (tests, linting, type checking)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    print("🧪 Learnobot Test Runner")
    print("=" * 25)
    
    # Install dependencies if requested
    if args.install_deps:
        if not install_test_dependencies():
            print("\n💥 Failed to install test dependencies")
            sys.exit(1)
        print()
    
    success = True
    
    # Run tests
    if not args.lint and not args.type_check or args.all:
        test_success, _ = run_pytest(
            test_path=args.test_path,
            coverage=args.coverage or args.all,
            verbose=args.verbose
        )
        if not test_success:
            success = False
        print()
    
    # Run linting
    if args.lint or args.all:
        lint_success = run_linting()
        if not lint_success:
            success = False
        print()
    
    # Run type checking
    if args.type_check or args.all:
        type_success, _ = run_type_checking()
        if not type_success:
            success = False
        print()
    
    # Final summary
    if success:
        print("🎉 All checks passed!")
        
        if args.coverage or args.all:
            print("\n📊 Coverage report generated in htmlcov/index.html")
    else:
        print("💥 Some checks failed!")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Testing cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)
