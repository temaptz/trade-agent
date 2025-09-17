#!/usr/bin/env python3
"""
Environment setup script for Bitcoin Trading Agent
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check Python version"""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required. Current version:", sys.version)
        return False
    print(f"✅ Python {sys.version.split()[0]} is compatible")
    return True

def install_requirements():
    """Install Python requirements"""
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found")
        return False
    
    return run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing Python requirements"
    )

def setup_environment_file():
    """Setup environment file"""
    print("📝 Setting up environment file...")
    
    if not Path(".env.example").exists():
        print("❌ .env.example not found")
        return False
    
    if not Path(".env").exists():
        shutil.copy(".env.example", ".env")
        print("✅ Created .env file from .env.example")
        print("⚠️  Please edit .env file with your API keys")
    else:
        print("✅ .env file already exists")
    
    return True

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = ["logs", "data", "exports", "backups"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created {directory}/ directory")
    
    return True

def check_ollama():
    """Check if Ollama is installed and running"""
    print("🤖 Checking Ollama...")
    
    # Check if Ollama is installed
    if not shutil.which("ollama"):
        print("❌ Ollama not found. Please install Ollama:")
        print("   curl -fsSL https://ollama.ai/install.sh | sh")
        return False
    
    print("✅ Ollama is installed")
    
    # Check if Ollama is running
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running")
        else:
            print("⚠️  Ollama is not running. Starting Ollama...")
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)  # Wait for Ollama to start
    except Exception:
        print("⚠️  Ollama is not running. Please start it manually:")
        print("   ollama serve")
        return False
    
    return True

def install_ollama_model():
    """Install required Ollama model"""
    print("📦 Installing Ollama model...")
    
    return run_command(
        "ollama pull llama3.1:8b",
        "Installing llama3.1:8b model"
    )

def run_tests():
    """Run tests to verify installation"""
    print("🧪 Running tests...")
    
    return run_command(
        f"{sys.executable} run_tests.py test",
        "Running tests"
    )

def main():
    """Main setup function"""
    print("=" * 60)
    print("🛠️  Bitcoin Trading Agent Environment Setup")
    print("=" * 60)
    
    steps = [
        ("Checking Python version", check_python_version),
        ("Installing requirements", install_requirements),
        ("Setting up environment file", setup_environment_file),
        ("Creating directories", create_directories),
        ("Checking Ollama", check_ollama),
        ("Installing Ollama model", install_ollama_model),
    ]
    
    for description, function in steps:
        print(f"\n📋 {description}...")
        if not function():
            print(f"\n❌ Setup failed at: {description}")
            print("Please fix the issue and run the setup again.")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ Environment setup completed successfully!")
    print("=" * 60)
    
    print("\n📝 Next steps:")
    print("1. Edit .env file with your Bybit API keys")
    print("2. Run: python scripts/start_agent.py")
    print("3. Or run: python main.py")
    
    # Ask if user wants to run tests
    try:
        response = input("\n🧪 Would you like to run tests to verify the installation? (y/n): ")
        if response.lower() in ['y', 'yes']:
            print("\n🧪 Running tests...")
            if run_tests():
                print("✅ All tests passed!")
            else:
                print("⚠️  Some tests failed, but setup is complete")
    except KeyboardInterrupt:
        print("\n⏹️  Setup completed without running tests")

if __name__ == "__main__":
    main()