#!/usr/bin/env python3
"""
Test runner script for document service

Usage:
    python run_tests.py                    # Run unit and integration tests
    python run_tests.py --unit             # Run only unit tests
    python run_tests.py --integration      # Run only integration tests
    python run_tests.py --e2e              # Run only E2E tests
    python run_tests.py --all              # Run all tests including E2E
    python run_tests.py --smoke            # Run smoke tests
    python run_tests.py --coverage         # Run with coverage report
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd: list[str]) -> int:
    """Run a command and return exit code"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run document service tests")
    
    # Test type selection
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument("--unit", action="store_true", help="Run only unit tests")
    test_group.add_argument("--integration", action="store_true", help="Run only integration tests")
    test_group.add_argument("--e2e", action="store_true", help="Run only E2E tests")
    test_group.add_argument("--all", action="store_true", help="Run all tests including E2E")
    test_group.add_argument("--smoke", action="store_true", help="Run smoke tests")
    
    # Options
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--parallel", "-n", type=int, help="Run tests in parallel (number of workers)")
    parser.add_argument("--failfast", "-x", action="store_true", help="Stop on first failure")
    
    args = parser.parse_args()
    
    # Build pytest command
    cmd = ["uv", "run", "pytest"]
    
    # Add verbosity
    if args.verbose:
        cmd.append("-vv")
    
    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    
    # Add fail fast
    if args.failfast:
        cmd.append("-x")
    
    # Add coverage
    if args.coverage:
        cmd.extend([
            "--cov=.",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-fail-under=80"
        ])
    
    # Select test types
    if args.unit:
        cmd.extend(["-m", "unit"])
    elif args.integration:
        cmd.extend(["-m", "integration"])
    elif args.e2e:
        cmd.extend(["-m", "e2e"])
    elif args.smoke:
        cmd.extend(["-m", "smoke"])
    elif args.all:
        cmd.extend(["-m", "unit or integration or e2e"])
    else:
        # Default: run unit and integration tests (exclude E2E)
        cmd.extend(["-m", "not e2e"])
    
    # Set environment for testing
    env = os.environ.copy()
    env.update({
        "FASTAPI_ENV": "testing",
        "DATABASE_ECHO": "false",
        "LOG_LEVEL": "WARNING"
    })
    
    # Run tests
    print("🧪 Running Document Service Tests")
    print("=" * 50)
    
    try:
        result = subprocess.run(cmd, env=env, cwd=Path(__file__).parent)
        exit_code = result.returncode
        
        if exit_code == 0:
            print("\n✅ All tests passed!")
            if args.coverage:
                print("📊 Coverage report generated in htmlcov/index.html")
        else:
            print(f"\n❌ Tests failed with exit code {exit_code}")
        
        return exit_code
        
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Error running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

