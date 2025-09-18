"""
Setup script for Bitcoin trading agent
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    return run_command("pip install -r requirements.txt", "Installing dependencies")

def setup_ollama():
    """Setup Ollama"""
    print("🤖 Setting up Ollama...")
    
    # Check if Ollama is installed
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama is already installed")
        else:
            print("📥 Installing Ollama...")
            if not run_command("curl -fsSL https://ollama.ai/install.sh | sh", "Installing Ollama"):
                return False
    except FileNotFoundError:
        print("📥 Installing Ollama...")
        if not run_command("curl -fsSL https://ollama.ai/install.sh | sh", "Installing Ollama"):
            return False
    
    # Start Ollama service
    print("🚀 Starting Ollama service...")
    if not run_command("ollama serve &", "Starting Ollama service"):
        return False
    
    # Wait a bit for service to start
    import time
    time.sleep(5)
    
    # Pull the model
    print("📥 Pulling Gemma model...")
    if not run_command("ollama pull gemma2:9b", "Pulling Gemma model"):
        return False
    
    return True

def setup_environment():
    """Setup environment configuration"""
    print("⚙️ Setting up environment...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("📋 Creating .env file from template...")
            with open(env_example, 'r') as f:
                content = f.read()
            with open(env_file, 'w') as f:
                f.write(content)
            print("✅ .env file created")
            print("⚠️  Please edit .env file with your API keys")
        else:
            print("❌ .env.example file not found")
            return False
    else:
        print("✅ .env file already exists")
    
    return True

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = ["logs", "data", "backups"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    return True

def test_installation():
    """Test the installation"""
    print("🧪 Testing installation...")
    
    try:
        # Test imports
        print("📦 Testing imports...")
        import pandas as pd
        import numpy as np
        import ccxt
        from langchain.tools import BaseTool
        from langgraph.graph import StateGraph
        print("✅ All imports successful")
        
        # Test Ollama connection
        print("🤖 Testing Ollama connection...")
        import requests
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                print("✅ Ollama connection successful")
            else:
                print("⚠️  Ollama connection failed")
        except Exception as e:
            print(f"⚠️  Ollama connection failed: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Bitcoin Trading Agent Setup")
    print("=" * 50)
    
    steps = [
        ("Python Version Check", check_python_version),
        ("Create Directories", create_directories),
        ("Install Dependencies", install_dependencies),
        ("Setup Environment", setup_environment),
        ("Setup Ollama", setup_ollama),
        ("Test Installation", test_installation)
    ]
    
    success_count = 0
    
    for step_name, step_func in steps:
        print(f"\n{'='*50}")
        print(f"Step: {step_name}")
        print('='*50)
        
        if step_func():
            success_count += 1
        else:
            print(f"❌ Step '{step_name}' failed")
            break
    
    print(f"\n{'='*50}")
    print("📊 Setup Summary")
    print('='*50)
    
    if success_count == len(steps):
        print("🎉 Setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Edit .env file with your Bybit API keys")
        print("2. Run: python demo.py")
        print("3. Run: python main.py single")
    else:
        print(f"❌ Setup failed at step {success_count + 1}")
        print("Please check the error messages above")
    
    return success_count == len(steps)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)