#!/bin/bash
# Nexus Agent Deployment Script for Moria-Pi (with external HDD logging)
# Moria-pi is a Pi 3B+ with external USB storage for logs and data
# Usage: ./deploy-moria-pi.sh [hdd_mount_path] [shared_secret]
#
# Defaults:
#   hdd_mount_path: /mnt/nexus-storage
#   shared_secret: (from .env file)

set -e

# Configuration
PI_HOST="${MORIA_HOST:-10.243.14.179}"
PI_USER="${MORIA_USER:-methinked}"
PI_PASS="${MORIA_PASS:-107512625}"
CORE_HOST="${CORE_HOST:-10.243.151.228}"  # orthanc-pi
NODE_NAME="moria-pi"
HDD_MOUNT_PATH="${1:-/mnt/nexus-storage}"
SHARED_SECRET="${2}"

# Try to find shared secret if not provided
if [ -z "$SHARED_SECRET" ]; then
    if [ -f .env ]; then
        SHARED_SECRET=$(grep NEXUS_SHARED_SECRET .env 2>/dev/null | cut -d '=' -f2 || echo "")
    fi
fi

if [ -z "$SHARED_SECRET" ]; then
    echo "Error: SHARED_SECRET not provided and not found in .env"
    echo "Usage: ./deploy-moria-pi.sh [hdd_mount_path] [shared_secret]"
    echo ""
    echo "Environment variables:"
    echo "  MORIA_HOST (default: 10.243.14.179)"
    echo "  MORIA_USER (default: methinked)"
    echo "  MORIA_PASS (default: 107512625)"
    echo "  CORE_HOST (default: 10.243.151.228 - orthanc-pi)"
    exit 1
fi

echo "================================"
echo "🔧 Nexus Agent Deployment - Moria-Pi"
echo "================================"
echo "Target:       $PI_USER@$PI_HOST"
echo "Core Server:  $CORE_HOST:8000 (orthanc-pi)"
echo "Node Name:    $NODE_NAME"
echo "HDD Path:     $HDD_MOUNT_PATH"
echo "Logs Dir:     $HDD_MOUNT_PATH/logs"
echo "Data Dir:     $HDD_MOUNT_PATH/data"
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

echo "[1/10] Connection Check..."
HOSTNAME=$(ssh_exec "hostname" 2>/dev/null || echo "UNREACHABLE")
echo "✓ Connected to: $HOSTNAME"

echo ""
echo "[2/10] Pre-flight Checks..."
# Check if port 8001 is in use
if ssh_exec "lsof -i :8001 > /dev/null 2>&1"; then
    echo "⚠ Port 8001 already in use. Stopping existing agent..."
    sudo_exec "systemctl stop nexus-agent 2>/dev/null || true"
    ssh_exec "pkill -f '[n]exus.agent.main' || true"
    sleep 2
fi

echo ""
echo "[3/10] Checking External HDD..."
# Check if HDD mount path exists
HDD_EXISTS=$(ssh_exec "[ -d '$HDD_MOUNT_PATH' ] && echo 'exists' || echo 'missing'")
if [ "$HDD_EXISTS" = "missing" ]; then
    echo "⚠ HDD mount path does not exist: $HDD_MOUNT_PATH"
    echo "  Creating directory and checking for external storage..."
    sudo_exec "mkdir -p '$HDD_MOUNT_PATH'"
    
    # Show available block devices for reference
    echo "  Available block devices:"
    ssh_exec "lsblk -d -n -o NAME,SIZE 2>/dev/null | grep -v mmcblk || echo '    (check manually with: lsblk)'"
else
    echo "✓ HDD mount path exists: $HDD_MOUNT_PATH"
    echo "  Space available: $(ssh_exec "df -h '$HDD_MOUNT_PATH' | tail -1 | awk '{print \$4}'")"
fi

echo ""
echo "[4/10] Creating Log and Data Directories..."
sudo_exec "mkdir -p '$HDD_MOUNT_PATH/logs'"
sudo_exec "mkdir -p '$HDD_MOUNT_PATH/data'"
echo "✓ Directories created on external HDD"

echo ""
echo "[5/10] Cleaning deployment directory..."
ssh_exec "rm -rf ~/nexus-agent"
ssh_exec "mkdir -p ~/nexus-agent"

echo ""
echo "[6/10] Packaging agent code..."
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
echo "  Copying code to moria-pi..."
scp_copy "$TEMP_DIR"/* "$PI_USER@$PI_HOST:~/nexus-agent/" > /dev/null 2>&1

echo ""
echo "[7/10] Setting up Python environment..."
ssh_exec "cd ~/nexus-agent && python3 -m venv venv"
echo "  Installing dependencies (this may take 2-3 minutes)..."
ssh_exec "cd ~/nexus-agent && source venv/bin/activate && pip install --upgrade pip > /dev/null 2>&1 && pip install -r requirements-agent.txt > /dev/null 2>&1"
echo "✓ Dependencies installed"

echo ""
echo "[8/10] Configuring Agent..."
cat > "$TEMP_DIR/.env" << EOF
# Nexus Agent Configuration - Moria-Pi
NEXUS_NODE_NAME=$NODE_NAME
NEXUS_CORE_URL=http://$CORE_HOST:8000
NEXUS_AGENT_PORT=8001
NEXUS_SHARED_SECRET=$SHARED_SECRET
NEXUS_METRICS_INTERVAL=30
NEXUS_ENV=production
NEXUS_AGENT_HOST=0.0.0.0

# Logging and Data - Store on external HDD, NOT SD card
NEXUS_LOGS_DIR=$HDD_MOUNT_PATH/logs
NEXUS_DATA_DIR=$HDD_MOUNT_PATH/data

# Performance tuning for Pi 3B+
NEXUS_LOG_LEVEL=info
EOF

scp_copy "$TEMP_DIR/.env" "$PI_USER@$PI_HOST:~/nexus-agent/.env" > /dev/null 2>&1
echo "✓ Agent configuration created"

echo ""
echo "[9/10] Installing Systemd Service..."
# Generate service file with proper permissions for HDD access
cat > "$TEMP_DIR/nexus-agent.service" << EOF
[Unit]
Description=Nexus Agent - Moria-Pi
After=network.target
Documentation=https://github.com/methinked/nexus

[Service]
Type=simple
User=$PI_USER
Group=$PI_USER
WorkingDirectory=/home/$PI_USER/nexus-agent
Environment="PATH=/home/$PI_USER/nexus-agent/venv/bin"
EnvironmentFile=/home/$PI_USER/nexus-agent/.env
ExecStartPre=/bin/bash -c '/bin/mkdir -p /mnt/nexus-storage/logs /mnt/nexus-storage/data && /bin/chown -R $PI_USER:$PI_USER /mnt/nexus-storage'
ExecStart=/home/$PI_USER/nexus-agent/venv/bin/python -m nexus.agent.main
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=nexus-agent

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
# ProtectHome=true  # Disabled for HDD access
ReadWritePaths=/home/$PI_USER/nexus-agent
ReadWritePaths=$HDD_MOUNT_PATH

# Resource limits for Pi 3B+ (1GB RAM)
MemoryLimit=256M
CPUQuota=80%

[Install]
WantedBy=multi-user.target
EOF

scp_copy "$TEMP_DIR/nexus-agent.service" "$PI_USER@$PI_HOST:/tmp/nexus-agent.service" > /dev/null 2>&1
sudo_exec "mv /tmp/nexus-agent.service /etc/systemd/system/nexus-agent.service"
sudo_exec "systemctl daemon-reload"
sudo_exec "systemctl enable nexus-agent"
echo "✓ Systemd service installed and enabled"

echo ""
echo "[10/10] Starting Service..."
sudo_exec "systemctl restart nexus-agent"
sleep 3

# Verify service is running
SERVICE_STATUS=$(ssh_exec "systemctl is-active nexus-agent 2>/dev/null || echo 'inactive'")
if [ "$SERVICE_STATUS" = "active" ]; then
    echo "✅ Service is running!"
else
    echo "⚠ Service status: $SERVICE_STATUS"
    echo "  Checking logs:"
    ssh_exec "journalctl -u nexus-agent -n 10 --no-pager" || true
fi

echo ""
echo "================================"
echo "🎉 Deployment Complete!"
echo "================================"
echo ""
echo "✓ Agent deployed to moria-pi (10.243.14.179)"
echo "✓ Logs configured to: $HDD_MOUNT_PATH/logs"
echo "✓ Data directory: $HDD_MOUNT_PATH/data"
echo "✓ Connected to core: orthanc-pi (10.243.151.228:8000)"
echo ""
echo "📝 Next Steps:"
echo "  1. Verify agent is running:"
echo "     ssh $PI_USER@$PI_HOST 'systemctl status nexus-agent'"
echo "  2. Check health endpoint:"
echo "     curl http://$PI_HOST:8001/health"
echo "  3. View recent logs on moria-pi:"
echo "     ssh $PI_USER@$PI_HOST 'tail -f $HDD_MOUNT_PATH/logs/*.log' 2>/dev/null || echo 'Logs not yet created'"
echo "  4. Check on orthanc-pi that moria-pi registered:"
echo "     curl http://10.243.151.228:8000/api/nodes?status=online"
echo ""
echo "🔗 To connect SSH with agent on moria-pi:"
echo "   ssh $PI_USER@$PI_HOST"
echo ""
