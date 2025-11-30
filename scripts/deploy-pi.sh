#!/bin/bash
# Nexus Agent Deployment Script for Raspberry Pi
# Usage: ./deploy-pi.sh <pi_host> <pi_user> <pi_password>

set -e

PI_HOST="${1:-10.243.14.179}"
PI_USER="${2:-methinked}"
PI_PASS="${3:-107512625}"
CORE_HOST="${4:-10.243.29.55}"  # Your laptop's ZeroTier IP

echo "=== Nexus Agent Deployment to Raspberry Pi ==="
echo "Target: $PI_USER@$PI_HOST"
echo "Core Server: $CORE_HOST:8000"
echo ""

# Helper function to run SSH commands
ssh_exec() {
    sshpass -p "$PI_PASS" ssh -o StrictHostKeyChecking=no "$PI_USER@$PI_HOST" "$@"
}

# Helper function to copy files
scp_copy() {
    sshpass -p "$PI_PASS" scp -o StrictHostKeyChecking=no -r "$@"
}

echo "[1/7] Testing SSH connection..."
ssh_exec "echo 'Connection successful to \$(hostname)'"

echo "[2/7] Creating deployment directory on Pi..."
ssh_exec "mkdir -p ~/nexus-agent && rm -rf ~/nexus-agent/*"

echo "[3/7] Copying agent code to Pi..."
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Create deployment package
mkdir -p "$TEMP_DIR/nexus"
cp -r nexus/agent "$TEMP_DIR/nexus/"
cp -r nexus/shared "$TEMP_DIR/nexus/"
cp nexus/__init__.py "$TEMP_DIR/nexus/"
cp requirements.txt "$TEMP_DIR/"
cp requirements-agent.txt "$TEMP_DIR/"
cp pyproject.toml "$TEMP_DIR/"

# Copy to Pi
scp_copy "$TEMP_DIR"/* "$PI_USER@$PI_HOST:~/nexus-agent/"

echo "[4/7] Creating Python virtual environment on Pi..."
ssh_exec "cd ~/nexus-agent && python3 -m venv venv"

echo "[5/7] Installing dependencies on Pi (this may take a while)..."
ssh_exec "cd ~/nexus-agent && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements-agent.txt"

echo "[6/7] Creating agent configuration..."
cat > "$TEMP_DIR/.env" << EOF
# Nexus Agent Configuration
NEXUS_NODE_NAME=moria-pi
NEXUS_CORE_URL=http://$CORE_HOST:8000
NEXUS_AGENT_PORT=8001
NEXUS_SHARED_SECRET=change-me-in-production
NEXUS_METRICS_INTERVAL=30
EOF

scp_copy "$TEMP_DIR/.env" "$PI_USER@$PI_HOST:~/nexus-agent/"

echo "[7/7] Creating startup script..."
cat > "$TEMP_DIR/start-agent.sh" << 'EOF'
#!/bin/bash
cd ~/nexus-agent
source venv/bin/activate
export PYTHONPATH=.
python3 -m nexus.agent.main
EOF

scp_copy "$TEMP_DIR/start-agent.sh" "$PI_USER@$PI_HOST:~/nexus-agent/"
ssh_exec "chmod +x ~/nexus-agent/start-agent.sh"

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "To start the agent on the Pi:"
echo "  ssh $PI_USER@$PI_HOST"
echo "  cd ~/nexus-agent"
echo "  ./start-agent.sh"
echo ""
echo "Or run it in the background:"
echo "  nohup ./start-agent.sh > agent.log 2>&1 &"
echo ""
echo "To check if it's running:"
echo "  curl http://$PI_HOST:8001/health"
echo ""
