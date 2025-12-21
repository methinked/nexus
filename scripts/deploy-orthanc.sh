#!/bin/bash
set -e

# Configuration
CORE_IP="10.243.14.179"
CORE_URL="http://${CORE_IP}:8000"
SHARED_SECRET="nexus-secret-key-change-in-production"
NODE_NAME="orthanc-pi"

echo "=== Deploying Nexus Agent to Orthanc-Pi ==="

# 1. Clean previous install
echo "[1/6] Cleaning previous installation..."
pkill -9 -f nexus.agent.main || true
rm -rf ~/nexus-agent
mkdir -p ~/nexus-agent

# 2. Move files from setup dir
echo "[2/6] Moving files..."
if [ -d "$HOME/nexus-setup" ]; then
    cp -r $HOME/nexus-setup/* $HOME/nexus-agent/
    rm -rf $HOME/nexus-setup
else
    echo "ERROR: Source files not found in ~/nexus-setup"
    exit 1
fi

cd ~/nexus-agent

# 3. Setup Python Environment
echo "[3/6] Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install -q --upgrade pip
# Install dependencies
pip install -q -r requirements-agent.txt
# Install local package
pip install -q -e .

# 4. Create Configuration
echo "[4/6] Configuring Agent..."
cat > .env << EOF
NEXUS_CORE_URL=$CORE_URL
NEXUS_SHARED_SECRET=$SHARED_SECRET
NEXUS_NODE_NAME=$NODE_NAME
NEXUS_AGENT_HOST=0.0.0.0
NEXUS_AGENT_PORT=8001
NEXUS_METRICS_INTERVAL=30
NEXUS_ENV=production
EOF

# 5. Connectivity Check
echo "[5/6] Checking connectivity to Core ($CORE_IP)..."
if ping -c 1 $CORE_IP &> /dev/null; then
    echo "   ✅ Core is reachable via ZeroTier"
else
    echo "   ⚠️  WARNING: Core ($CORE_IP) not reachable! Agent might fail to register."
fi

# 6. Start Agent (Background)
echo "[6/6] Starting Agent..."
nohup python -m nexus.agent.main > agent.log 2>&1 &

echo "=== Deployment Complete ==="
sleep 2
echo "Agent Status:"
ps aux | grep nexus.agent.main | grep -v grep
