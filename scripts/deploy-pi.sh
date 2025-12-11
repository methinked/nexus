#!/bin/bash
# Nexus Agent Deployment Script for Raspberry Pi/Debian
# Usage: ./deploy-pi.sh <pi_host> <pi_user> <pi_password> <core_host> <node_name> [shared_secret]

set -e

PI_HOST="${1:-10.243.14.179}"
PI_USER="${2:-methinked}"
PI_PASS="${3:-107512625}"
CORE_HOST="${4:-10.243.29.55}"
NODE_NAME="${5:-nexus-node}"
SHARED_SECRET="${6}"

# Try to find shared secret if not provided
if [ -z "$SHARED_SECRET" ]; then
    if [ -f .env ]; then
        SHARED_SECRET=$(grep NEXUS_SHARED_SECRET .env | cut -d '=' -f2)
    fi
fi

if [ -z "$SHARED_SECRET" ]; then
    echo "Error: SHARED_SECRET not provided and not found in .env"
    echo "Usage: ./deploy-pi.sh <pi_host> <pi_user> <pi_password> <core_host> <node_name> [shared_secret]"
    exit 1
fi

echo "=== Nexus Agent Deployment ==="
echo "Target: $PI_USER@$PI_HOST"
echo "Core Server: $CORE_HOST:8000"
echo "Node Name: $NODE_NAME"
echo ""

# Helper function to run SSH commands
ssh_exec() {
    sshpass -p "$PI_PASS" ssh -o StrictHostKeyChecking=no "$PI_USER@$PI_HOST" "$@"
}

# Helper function to run Sudo commands
sudo_exec() {
    ssh_exec "echo '$PI_PASS' | sudo -S -p '' $@"
}

# Helper function to copy files
scp_copy() {
    sshpass -p "$PI_PASS" scp -o StrictHostKeyChecking=no -r "$@"
}

echo "[1/8] Connection Check..."
ssh_exec "echo 'Connection successful to \$(hostname)'"

echo "[2/8] Pre-flight Checks..."
# Check if port 8001 is in use
if ssh_exec "lsof -i :8001 > /dev/null"; then
    echo "Warning: Port 8001 is in use on target. Attempting to stop existing agent..."
    # Attempt to stop service if it exists (ignore failure)
    sudo_exec "systemctl stop nexus-agent 2>/dev/null || true"
    ssh_exec "pkill -f nexus.agent.main || true"
fi

echo "[3/8] Cleaning deployment directory..."
ssh_exec "mkdir -p ~/nexus-agent"

echo "[4/8] Packaging agent code..."
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

mkdir -p "$TEMP_DIR/nexus"
cp -r nexus/agent "$TEMP_DIR/nexus/"
cp -r nexus/shared "$TEMP_DIR/nexus/"
cp nexus/__init__.py "$TEMP_DIR/nexus/"
cp requirements.txt "$TEMP_DIR/"
cp requirements-agent.txt "$TEMP_DIR/"
cp pyproject.toml "$TEMP_DIR/"

# Copy to Pi
scp_copy "$TEMP_DIR"/* "$PI_USER@$PI_HOST:~/nexus-agent/"

echo "[5/8] Setting up Python environment..."
ssh_exec "cd ~/nexus-agent && python3 -m venv venv"
# Install dependencies (quietly)
echo "Installing dependencies (this may take a minute)..."
ssh_exec "cd ~/nexus-agent && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements-agent.txt > /dev/null"

echo "[6/8] Configuring Agent..."
cat > "$TEMP_DIR/.env" << EOF
# Nexus Agent Configuration
NEXUS_NODE_NAME=$NODE_NAME
NEXUS_CORE_URL=http://$CORE_HOST:8000
NEXUS_AGENT_PORT=8001
NEXUS_SHARED_SECRET=$SHARED_SECRET
NEXUS_METRICS_INTERVAL=30
NEXUS_ENV=production
NEXUS_AGENT_HOST=0.0.0.0
EOF

scp_copy "$TEMP_DIR/.env" "$PI_USER@$PI_HOST:~/nexus-agent/"

echo "[7/8] Installing Systemd Service..."
# Generate service file
cat > "$TEMP_DIR/nexus-agent.service" << EOF
[Unit]
Description=Nexus Agent
After=network.target

[Service]
Type=simple
User=$PI_USER
WorkingDirectory=/home/$PI_USER/nexus-agent
Environment="PATH=/home/$PI_USER/nexus-agent/venv/bin"
EnvironmentFile=/home/$PI_USER/nexus-agent/.env
ExecStart=/home/$PI_USER/nexus-agent/venv/bin/python -m nexus.agent.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=nexus-agent

# Security hardening
NoNewPrivileges=true
ProtectSystem=full
# ProtectHome=true # Disabled because we run in home dir
ReadWritePaths=/home/$PI_USER/nexus-agent

[Install]
WantedBy=multi-user.target
EOF

scp_copy "$TEMP_DIR/nexus-agent.service" "$PI_USER@$PI_HOST:/tmp/nexus-agent.service"
sudo_exec "mv /tmp/nexus-agent.service /etc/systemd/system/nexus-agent.service"
sudo_exec "systemctl daemon-reload"
sudo_exec "systemctl enable nexus-agent"

echo "[8/8] Starting Service..."
sudo_exec "systemctl restart nexus-agent"

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "Check status:"
echo "  ssh $PI_USER@$PI_HOST 'systemctl status nexus-agent'"
echo "  curl http://$PI_HOST:8001/health"
echo ""
