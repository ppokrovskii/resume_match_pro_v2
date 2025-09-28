#!/usr/bin/env python3
"""
Script to run E2E tests
Usage: 
  python run_e2e.py                    # Run all E2E tests
  python run_e2e.py --smoke            # Run only smoke E2E tests
  python run_e2e.py --critical         # Run only critical E2E tests
  python run_e2e.py --env local        # Run against local environment
"""

import subprocess
import sys
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Run E2E tests")
    parser.add_argument("--smoke", action="store_true", help="Run only smoke tests")
    parser.add_argument("--critical", action="store_true", help="Run only critical tests")
    parser.add_argument("--full", action="store_true", help="Run full test suite")
    parser.add_argument("--env", choices=["local", "staging", "production"], 
                       default="local", help="Target environment")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Build pytest command
    cmd = ["uv", "run", "pytest", "tests/e2e/", "-m", "e2e"]
    
    # Add marker filters
    markers = []
    if args.smoke:
        markers.append("smoke")
    if args.critical:
        markers.append("critical")
    if args.full:
        markers.append("full")
    
    if markers:
        cmd.extend(["-m", f"e2e and ({' or '.join(markers)})"])
    
    # Add environment
    if args.env:
        cmd.extend(["--env", args.env])
    
    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Add other useful options
    cmd.extend(["--tb=short", "--no-header"])
    
    print(f"Running E2E tests against {args.env} environment...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    # Run the command
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
