#!/bin/bash

# LLM Memory Agent - Quick Start Script

echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║           LLM Memory Agent - Quick Start                ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Navigate to project root
cd "$(dirname "$0")/.."

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then 
    echo "✓ Python $python_version detected"
else
    echo "✗ Python 3.11+ required. Found: $python_version"
    exit 1
fi

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env created from template"
    echo ""
    echo "⚠️  Please edit .env and add your OpenAI API key:"
    echo "   OPENAI_API_KEY=your_key_here"
    echo ""
    read -p "Press Enter when you've added your API key..."
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Run tests
echo ""
echo "Running tests..."
PYTHONPATH=. pytest tests/test_agent.py -v --tb=short

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ All tests passed!"
else
    echo ""
    echo "⚠️  Some tests failed. Check the output above."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start server
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                  Starting Server                         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Server will start on: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

PYTHONPATH=. python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
