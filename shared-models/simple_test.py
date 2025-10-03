#!/usr/bin/env python3
"""
Simple local test script for shared-models package.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, check=True):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(f"   stdout: {result.stdout.strip()}")
    if result.stderr:
        print(f"   stderr: {result.stderr.strip()}")
    
    if check and result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        return False
    
    return result.returncode == 0


def test_basic_functionality():
    """Test basic functionality."""
    print("\nTesting basic functionality...")
    
    # Test imports
    result = run_command('python -c "from shared_models.generated.document_service import Feature; print(\'Import successful\')"')
    if not result:
        return False
    
    # Test model creation
    result = run_command('python -c "from shared_models.generated.document_service import Feature; f = Feature(name=\'Test\', type=\'skill\'); print(f\'Feature: {f.name}\')"')
    if not result:
        return False
    
    return True


def test_package_building():
    """Test package building."""
    print("\nTesting package building...")
    
    # Install build dependencies
    if not run_command("pip install build"):
        return False
    
    # Build package
    if not run_command("python -m build"):
        return False
    
    print("Package built successfully")
    return True


def main():
    """Run tests."""
    print("Shared Models Local Test")
    print("=" * 30)
    
    # Check we're in the right directory
    if not Path("pyproject.toml").exists():
        print("Error: Not in shared-models directory")
        return 1
    
    # Install dependencies
    print("\nInstalling dependencies...")
    if not run_command("python -m pip install --upgrade pip"):
        return 1
    
    if not run_command("pip install -e ."):
        return 1
    
    # Run tests
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Package Building", test_package_building),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"{test_name}: PASSED")
                passed += 1
            else:
                print(f"{test_name}: FAILED")
                failed += 1
        except Exception as e:
            print(f"{test_name}: FAILED ({e})")
            failed += 1
    
    print("-" * 30)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
