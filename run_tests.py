"""
Test runner script for Bitcoin Trading Agent
"""
import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    """Run all tests with proper configuration"""
    try:
        # Ensure we're in the project root
        project_root = Path(__file__).parent
        os.chdir(project_root)
        
        print("🧪 Running Bitcoin Trading Agent Tests...")
        print("=" * 50)
        
        # Run unit tests
        print("\n📊 Running Unit Tests...")
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "-v", 
            "--tb=short",
            "--disable-warnings",
            "-m", "unit"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Run integration tests if unit tests pass
        if result.returncode == 0:
            print("\n🔗 Running Integration Tests...")
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "tests/", 
                "-v", 
                "--tb=short",
                "--disable-warnings",
                "-m", "integration"
            ], capture_output=True, text=True)
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
        
        # Run slow tests separately
        print("\n⏳ Running Slow Tests...")
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "-v", 
            "--tb=short",
            "--disable-warnings",
            "-m", "slow",
            "--timeout=300"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Generate coverage report
        print("\n📈 Generating Coverage Report...")
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "--cov=.",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--disable-warnings"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        print("\n✅ Test run completed!")
        print("📊 Coverage report generated in htmlcov/index.html")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_specific_test(test_name):
    """Run a specific test"""
    try:
        print(f"🧪 Running specific test: {test_name}")
        
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            f"tests/{test_name}", 
            "-v", 
            "--tb=short",
            "--disable-warnings"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running specific test: {e}")
        return False

def run_linting():
    """Run code linting"""
    try:
        print("🔍 Running Code Linting...")
        
        # Run flake8
        result = subprocess.run([
            sys.executable, "-m", "flake8", 
            ".", 
            "--max-line-length=120",
            "--ignore=E203,W503"
        ], capture_output=True, text=True)
        
        if result.stdout:
            print("FLAKE8 Issues:")
            print(result.stdout)
        
        # Run black check
        result = subprocess.run([
            sys.executable, "-m", "black", 
            "--check", 
            "."
        ], capture_output=True, text=True)
        
        if result.stdout:
            print("BLACK Issues:")
            print(result.stdout)
        
        print("✅ Linting completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error running linting: {e}")
        return False

def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            success = run_tests()
        elif command == "lint":
            success = run_linting()
        elif command.startswith("test:"):
            test_name = command.split(":")[1]
            success = run_specific_test(test_name)
        else:
            print(f"Unknown command: {command}")
            print("Available commands: test, lint, test:<test_name>")
            success = False
    else:
        success = run_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()