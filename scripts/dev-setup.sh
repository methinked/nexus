#!/bin/bash

# Nexus Development Environment Setup Script
# This script sets up the development environment for Nexus

set -e  # Exit on error

echo "🚀 Setting up Nexus development environment..."

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    echo "❌ Python 3.11+ is required. Found: $python_version"
    exit 1
fi
echo "✅ Python version OK: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements-dev.txt

# Install package in editable mode
echo "📦 Installing Nexus in editable mode..."
pip install -e .

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created - please update with your values"
else
    echo "✅ .env file already exists"
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data logs

# Initialize git if not already initialized
if [ ! -d ".git" ]; then
    echo "🔧 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit: Project structure and configuration"
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already initialized"
fi

# Install pre-commit hooks
if command -v pre-commit &> /dev/null; then
    echo "🪝 Installing pre-commit hooks..."
    pre-commit install
    echo "✅ Pre-commit hooks installed"
else
    echo "⚠️  pre-commit not found, skipping hook installation"
fi

echo ""
echo "✨ Development environment setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Activate the virtual environment: source venv/bin/activate"
echo "   2. Update .env with your configuration"
echo "   3. Start development:"
echo "      - Core:  uvicorn nexus.core.main:app --reload"
echo "      - Agent: uvicorn nexus.agent.main:app --port 8001 --reload"
echo "      - CLI:   nexus --help"
echo ""
echo "📖 Read docs/architecture.md for more information"
echo ""
