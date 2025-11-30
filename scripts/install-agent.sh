#!/bin/bash
# Nexus Agent Installation Script
# This script sets up the Nexus Agent on a Raspberry Pi

set -e

echo "==================================="
echo "  Nexus Agent Installation"
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
pip install -q -r requirements-agent.txt
pip install -q -e .

# Create data directory
mkdir -p data

# Prompt for configuration
echo ""
echo "⚙️  Agent Configuration"
echo ""

if [ ! -f ".env" ]; then
    # Get Core URL
    read -p "Enter Core server URL (e.g., http://192.168.1.100:8000): " CORE_URL

    # Get shared secret
    read -sp "Enter shared secret (from Core server .env): " SHARED_SECRET
    echo ""

    # Get node name
    DEFAULT_NAME=$(hostname)
    read -p "Enter node name [$DEFAULT_NAME]: " NODE_NAME
    NODE_NAME=${NODE_NAME:-$DEFAULT_NAME}

    cat > .env << EOF
# Nexus Agent Configuration
# Generated on $(date)

# Core Server
NEXUS_CORE_URL=$CORE_URL
NEXUS_SHARED_SECRET=$SHARED_SECRET

# Agent Settings
NEXUS_NODE_NAME=$NODE_NAME
NEXUS_AGENT_HOST=0.0.0.0
NEXUS_AGENT_PORT=8001
NEXUS_ENV=production
NEXUS_LOG_LEVEL=info

# Metrics
NEXUS_METRICS_INTERVAL=30
EOF

    echo "✅ Configuration created at .env"
else
    echo "✅ Configuration already exists at .env"
fi

# Test connection to Core
echo ""
echo "🔍 Testing connection to Core..."
source .env
CORE_HEALTH=$(curl -s -f -m 5 "$NEXUS_CORE_URL/health" 2>/dev/null || echo "FAILED")

if [[ $CORE_HEALTH == *"healthy"* ]]; then
    echo "✅ Successfully connected to Core server"
else
    echo "⚠️  Warning: Could not reach Core server at $NEXUS_CORE_URL"
    echo "   Make sure Core is running and reachable from this machine"
fi

echo ""
echo "==================================="
echo "  Installation Complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo "  1. Review configuration: cat .env"
echo "  2. Start Agent:"
echo "     source venv/bin/activate"
echo "     python -m nexus.agent.main"
echo ""
echo "  3. Or install as systemd service:"
echo "     sudo cp docs/systemd/nexus-agent.service /etc/systemd/system/"
echo "     sudo systemctl enable nexus-agent"
echo "     sudo systemctl start nexus-agent"
echo ""
echo "  4. Verify registration on Core:"
echo "     nexus node list"
echo ""
