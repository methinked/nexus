#!/bin/bash
# Nexus Agent Setup Script
# Installs dependencies, sets up Docker, and configures the agent.

set -e

echo "🚀 Starting Nexus Agent Setup..."

# 1. Update System
echo "📦 Updating system packages..."
sudo apt-get update

# 2. Check & Install Docker
if ! command -v docker &> /dev/null; then
    echo "🐳 Docker not found. Installing..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
    echo "✅ Docker installed successfully."
else
    echo "✅ Docker is already installed."
fi

# 3. Configure Permissions
echo "🔑 Configuring permissions..."
CURRENT_USER=$(whoami)
if ! groups $CURRENT_USER | grep -q "docker"; then
    echo "➕ Adding user $CURRENT_USER to docker group..."
    sudo usermod -aG docker $CURRENT_USER
    echo "⚠️  User added to docker group. You may need to re-login for this to take effect."
else
    echo "✅ User $CURRENT_USER is already in docker group."
fi

# 4. Install System Dependencies
echo "🛠️  Installing system dependencies..."
sudo apt-get install -y python3-venv python3-pip git libatlas-base-dev

# 5. Setup Python Environment
echo "🐍 Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created."
fi

source venv/bin/activate
pip install --upgrade pip wheel
pip install -r requirements.txt

echo "✨ Nexus Agent setup complete!"
echo "➡️  Run ./start-agent.sh to launch."
