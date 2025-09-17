#!/bin/bash

# AI Trading Bot Runner Script

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./install.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please copy .env.example to .env and configure it."
    exit 1
fi

# Check if Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "🦙 Starting Ollama service..."
    ollama serve &
    sleep 5
fi

# Parse command line arguments
MODE=${1:-"single"}
INTERVAL=${2:-30}

case $MODE in
    "single")
        echo "🤖 Running single trading cycle..."
        python main.py single
        ;;
    "continuous")
        echo "🤖 Running continuous trading (every $INTERVAL minutes)..."
        python main.py continuous $INTERVAL
        ;;
    "scheduled")
        echo "🤖 Running scheduled trading..."
        python main.py scheduled
        ;;
    "test")
        echo "🧪 Running bot tests..."
        python test_bot.py
        ;;
    *)
        echo "Usage: $0 [single|continuous|scheduled|test] [interval]"
        echo "  single      - Run single trading cycle"
        echo "  continuous  - Run continuously with specified interval (default: 30 minutes)"
        echo "  scheduled   - Run on schedule (every 30 minutes)"
        echo "  test        - Run tests"
        exit 1
        ;;
esac