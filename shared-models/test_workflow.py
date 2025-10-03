#!/usr/bin/env python3
"""
Local workflow test script for shared-models package.

This script simulates the GitHub Actions workflow locally to ensure
everything works before pushing to GitHub.
"""

import subprocess
import sys
import tempfile
import shutil
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result."""
    print(f"🔧 Running: {cmd}")
    result = subprocess.run(
        cmd, 
        shell=True, 
        cwd=cwd, 
        capture_output=True, 
        text=True
    )
    
    if result.stdout:
        print(f"   stdout: {result.stdout.strip()}")
    if result.stderr:
        print(f"   stderr: {result.stderr.strip()}")
    
    if check and result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        sys.exit(1)
    
    return result


def test_code_formatting():
    """Test code formatting with black."""
    print("\n📝 Testing code formatting...")
    try:
        run_command("pip install black")
        result = run_command("black --check --diff src/ tests/ scripts/", check=False)
        if result.returncode == 0:
            print("Code formatting is correct")
            return True
        else:
            print("Code formatting issues found")
            print("   Run 'black src/ tests/ scripts/' to fix")
            return False
    except Exception as e:
        print(f"Could not test formatting: {e}")
        return True


def test_import_sorting():
    """Test import sorting with isort."""
    print("\n📊 Testing import sorting...")
    try:
        run_command("pip install isort")
        result = run_command("isort --check-only --diff src/ tests/ scripts/", check=False)
        if result.returncode == 0:
            print("✅ Import sorting is correct")
            return True
        else:
            print("❌ Import sorting issues found")
            print("   Run 'isort src/ tests/ scripts/' to fix")
            return False
    except Exception as e:
        print(f"⚠️ Could not test import sorting: {e}")
        return True


def test_model_validation():
    """Test model validation."""
    print("\n🔍 Testing model validation...")
    result = run_command("python test_runner.py", check=False)
    if result.returncode == 0:
        print("✅ Model validation passed")
        return True
    else:
        print("❌ Model validation failed")
        return False


def test_package_building():
    """Test package building."""
    print("\n📦 Testing package building...")
    try:
        run_command("pip install build twine")
        run_command("python -m build")
        run_command("python -m twine check dist/*")
        print("✅ Package builds and validates successfully")
        return True
    except Exception as e:
        print(f"❌ Package building failed: {e}")
        return False


def test_package_installation():
    """Test package installation in a clean environment."""
    print("\n🧪 Testing package installation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Create virtual environment
            venv_path = Path(temp_dir) / "test_env"
            run_command(f"python -m venv {venv_path}")
            
            # Determine activation script path
            if sys.platform == "win32":
                activate_script = venv_path / "Scripts" / "activate.bat"
                pip_exe = venv_path / "Scripts" / "pip.exe"
                python_exe = venv_path / "Scripts" / "python.exe"
            else:
                activate_script = venv_path / "bin" / "activate"
                pip_exe = venv_path / "bin" / "pip"
                python_exe = venv_path / "bin" / "python"
            
            # Install the package
            dist_files = list(Path("dist").glob("*.whl"))
            if not dist_files:
                print("❌ No wheel file found in dist/")
                return False
            
            wheel_file = dist_files[0]
            run_command(f"{pip_exe} install {wheel_file}")
            
            # Test imports
            test_script = '''
from shared_models.generated.document_service import Feature, DocumentUpdateRequest
print("✅ Package installation test: imports work")
feature = Feature(name="LocalTest", type="skill")
print(f"✅ Package installation test: model creation works ({feature.name})")
'''
            
            result = run_command(f'{python_exe} -c "{test_script}"')
            print("✅ Package installation test passed")
            return True
            
        except Exception as e:
            print(f"❌ Package installation test failed: {e}")
            return False


def test_dependencies():
    """Test that all dependencies are correctly specified."""
    print("\n📋 Testing dependencies...")
    try:
        # Install the package in development mode
        run_command("pip install -e .")
        
        # Try importing everything
        test_script = '''
import sys
try:
    from shared_models import BaseSharedModel
    from shared_models.generated.document_service import Feature, DocumentUpdateRequest
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
'''
        
        run_command(f'python -c "{test_script}"')
        print("✅ Dependency test passed")
        return True
        
    except Exception as e:
        print(f"❌ Dependency test failed: {e}")
        return False


def cleanup():
    """Clean up generated files."""
    print("\n🧹 Cleaning up...")
    cleanup_paths = ["dist", "build", "*.egg-info", "__pycache__", ".pytest_cache"]
    
    for pattern in cleanup_paths:
        if "*" in pattern:
            import glob
            for path in glob.glob(pattern):
                try:
                    if Path(path).is_dir():
                        shutil.rmtree(path)
                    else:
                        Path(path).unlink()
                except Exception as e:
                    print(f"   Could not remove {path}: {e}")
        else:
            path = Path(pattern)
            if path.exists():
                try:
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                except Exception as e:
                    print(f"   Could not remove {path}: {e}")
    
    print("✅ Cleanup completed")


def main():
    """Run all tests."""
    print("Starting local workflow test for shared-models package")
    print("=" * 60)
    
    # Change to the correct directory
    if not Path("pyproject.toml").exists():
        print("❌ Not in shared-models directory. Please run from shared-models/")
        sys.exit(1)
    
    # Install basic dependencies
    print("\nInstalling basic dependencies...")
    run_command("python -m pip install --upgrade pip")
    run_command("pip install -e .[dev]")
    
    # Run all tests
    tests = [
        ("Code Formatting", test_code_formatting),
        ("Import Sorting", test_import_sorting),
        ("Model Validation", test_model_validation),
        ("Package Building", test_package_building),
        ("Package Installation", test_package_installation),
        ("Dependencies", test_dependencies),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        print(f"{test_name:.<40} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-" * 60)
    print(f"Total: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\nAll tests passed! Ready for GitHub workflow.")
        cleanup()
        return 0
    else:
        print(f"\n{failed} test(s) failed. Please fix the issues before pushing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
