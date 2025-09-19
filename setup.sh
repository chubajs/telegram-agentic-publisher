#!/bin/bash

# Setup script for Telegram Agentic Publisher

echo "================================================"
echo "  Telegram Agentic Publisher Setup"
echo "================================================"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or higher is required (found $python_version)"
    exit 1
fi

echo "✅ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Install package in development mode
echo "Installing telegram-agentic-publisher..."
pip install -e .

# Create necessary directories
echo "Creating data directories..."
mkdir -p data/sessions
mkdir -p data/media_cache
mkdir -p logs

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  Please edit .env file and add your Telegram API credentials:"
    echo "   - TELEGRAM_API_ID"
    echo "   - TELEGRAM_API_HASH"
    echo ""
    echo "   Get them from: https://my.telegram.org/apps"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "================================================"
echo "  Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Telegram API credentials"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Authenticate: telegram-publisher auth -p +YOUR_PHONE"
echo "4. Start posting: telegram-publisher post @channel -t 'Hello!'"
echo ""
echo "For more information, see README.md"