#!/bin/bash
# Nexus Core Installation Script
# This script sets up the Nexus Core server on a central machine

set -e

echo "==================================="
echo "  Nexus Core Installation"
echo "==================================="
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]; }; then
    echo "❌ Error: Python 3.11+ required (found $PYTHON_VERSION)"
    exit 1
fi

echo "✅ Python version: $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
pip install -q -e .

# Create data directory
mkdir -p data

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env configuration..."

    # Generate secrets
    SECRET1=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    SECRET2=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

    cat > .env << EOF
# Nexus Core Configuration
# Generated on $(date)

# Security - CHANGE THESE IN PRODUCTION
NEXUS_SHARED_SECRET=$SECRET1
NEXUS_JWT_SECRET_KEY=$SECRET2

# Server Settings
NEXUS_CORE_HOST=0.0.0.0
NEXUS_CORE_PORT=8000
NEXUS_ENV=production
NEXUS_LOG_LEVEL=info

# Database
NEXUS_DATABASE_URL=sqlite:///data/nexus.db
EOF

    echo "✅ Configuration created at .env"
    echo "   IMPORTANT: Keep these secrets safe!"
else
    echo "✅ Configuration already exists at .env"
fi

# Initialize database
echo "🗄️  Initializing database..."
python3 -c "from nexus.core.db import init_db; init_db()" 2>/dev/null || true

echo ""
echo "==================================="
echo "  Installation Complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo "  1. Review configuration: cat .env"
echo "  2. Start Core server:"
echo "     source venv/bin/activate"
echo "     python -m nexus.core.main"
echo ""
echo "  3. Or install as systemd service:"
echo "     sudo cp docs/systemd/nexus-core.service /etc/systemd/system/"
echo "     sudo systemctl enable nexus-core"
echo "     sudo systemctl start nexus-core"
echo ""
echo "  4. Configure CLI on other machines:"
echo "     nexus config init"
echo ""
