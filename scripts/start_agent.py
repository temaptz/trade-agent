#!/usr/bin/env python3
"""
Startup script for Bitcoin Trading Agent
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    # Check if .env file exists
    if not Path(".env").exists():
        print("❌ .env file not found. Please copy .env.example to .env and configure it.")
        return False
    
    # Check if logs directory exists
    logs_dir = Path("logs")
    if not logs_dir.exists():
        logs_dir.mkdir()
        print("✅ Created logs directory")
    
    # Check if Ollama is running
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running")
        else:
            print("❌ Ollama is not responding properly")
            return False
    except Exception:
        print("❌ Ollama is not running. Please start Ollama first:")
        print("   ollama serve")
        return False
    
    # Check if required model is available
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = response.json().get("models", [])
        model_names = [model["name"] for model in models]
        
        if not any("llama3.1:8b" in name for name in model_names):
            print("❌ llama3.1:8b model not found. Please install it:")
            print("   ollama pull llama3.1:8b")
            return False
        else:
            print("✅ Required model is available")
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return False
    
    print("✅ All requirements met")
    return True

def start_agent():
    """Start the trading agent"""
    print("🚀 Starting Bitcoin Trading Agent...")
    
    try:
        # Start the agent
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n⏹️  Agent stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting agent: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def main():
    """Main startup function"""
    print("=" * 50)
    print("🤖 Bitcoin Trading Agent Startup")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements check failed. Please fix the issues above.")
        sys.exit(1)
    
    # Start agent
    print("\n🚀 Starting agent...")
    if not start_agent():
        print("\n❌ Failed to start agent")
        sys.exit(1)
    
    print("\n✅ Agent startup completed")

if __name__ == "__main__":
    main()