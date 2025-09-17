#!/bin/bash

# AI Trading Bot Installation Script

echo "🤖 Installing AI Trading Bot..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python version $python_version is too old. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python $python_version detected"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "🦙 Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
    
    # Start Ollama service
    echo "🚀 Starting Ollama service..."
    ollama serve &
    OLLAMA_PID=$!
    
    # Wait for Ollama to start
    sleep 10
    
    # Pull the required model
    echo "📥 Downloading Gemma2 model (this may take a while)..."
    ollama pull gemma2:9b
    
    # Stop the background Ollama process
    kill $OLLAMA_PID
else
    echo "✅ Ollama is already installed"
    
    # Check if model is available
    if ! ollama list | grep -q "gemma2:9b"; then
        echo "📥 Downloading Gemma2 model..."
        ollama pull gemma2:9b
    else
        echo "✅ Gemma2 model is already available"
    fi
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p data

# Copy environment file
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys and configuration"
else
    echo "✅ .env file already exists"
fi

# Make scripts executable
chmod +x install.sh
chmod +x run_bot.sh

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Bybit API keys"
echo "2. Run tests: python test_bot.py"
echo "3. Start trading: python main.py single"
echo ""
echo "For more information, see README.md"