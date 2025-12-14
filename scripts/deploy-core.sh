#!/bin/bash
# Nexus Core Deployment Script
# Usage: ./deploy-core.sh <server_host> <server_user> <server_password>

set -e

SERVER_HOST="${1:-10.243.151.228}"
SERVER_USER="${2:-methinked}"
SERVER_PASS="${3:-107512625}"

echo "=== Nexus Core Deployment ==="
echo "Target: $SERVER_USER@$SERVER_HOST"
echo ""

# Helper function to run SSH commands
ssh_exec() {
    sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_HOST" "$@"
}

# Helper function to run Sudo commands
sudo_exec() {
    ssh_exec "echo '$SERVER_PASS' | sudo -S -p '' $@"
}

# Helper function to copy files
scp_copy() {
    sshpass -p "$SERVER_PASS" scp -o StrictHostKeyChecking=no -r "$@"
}

echo "[1/7] Connection Check..."
ssh_exec "echo 'Connection successful to \$(hostname)'"

echo "[2/7] Pre-flight Checks..."
if ssh_exec "lsof -i :8000 > /dev/null"; then
    echo "Warning: Port 8000 is in use. Stopping existing service..."
    sudo_exec "systemctl stop nexus-core 2>/dev/null || true"
    ssh_exec "pkill -f nexus.core.main || true"
fi

echo "[3/7] Cleaning deployment directory..."
ssh_exec "mkdir -p ~/nexus-core"

echo "[4/7] Packaging core code..."
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

mkdir -p "$TEMP_DIR/nexus"
cp -r nexus/core "$TEMP_DIR/nexus/"
cp -r nexus/shared "$TEMP_DIR/nexus/"
cp -r nexus/web "$TEMP_DIR/nexus/"
cp nexus/__init__.py "$TEMP_DIR/nexus/"
cp requirements.txt "$TEMP_DIR/"
cp pyproject.toml "$TEMP_DIR/"

# Copy to Server
scp_copy "$TEMP_DIR"/* "$SERVER_USER@$SERVER_HOST:~/nexus-core/"

echo "[5/7] Setting up Python environment..."
ssh_exec "cd ~/nexus-core && python3 -m venv venv"
echo "Installing dependencies..."
ssh_exec "cd ~/nexus-core && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt > /dev/null && pip install jinja2 uvicorn"

echo "[6/7] Configuring Core..."
# Generate .env
cat > "$TEMP_DIR/.env" << EOF
# Nexus Core Configuration
NEXUS_CORE_URL=http://$SERVER_HOST:8000
NEXUS_SHARED_SECRET=nexus-secret-change-me
NEXUS_JWT_SECRET_KEY=nexus-jwt-secret-change-me-min-32-chars
NEXUS_ENV=production
NEXUS_HOST=0.0.0.0
NEXUS_PORT=8000
NEXUS_DB_PATH=data/nexus.db
EOF
scp_copy "$TEMP_DIR/.env" "$SERVER_USER@$SERVER_HOST:~/nexus-core/"

# Initialize DB
ssh_exec "cd ~/nexus-core && source venv/bin/activate && python3 -m nexus.core.db.init_db || true"

echo "[7/7] Installing Systemd Service..."
cat > "$TEMP_DIR/nexus-core.service" << EOF
[Unit]
Description=Nexus Core Server
After=network.target

[Service]
Type=simple
User=$SERVER_USER
WorkingDirectory=/home/$SERVER_USER/nexus-core
Environment="PATH=/home/$SERVER_USER/nexus-core/venv/bin"
EnvironmentFile=/home/$SERVER_USER/nexus-core/.env
ExecStart=/home/$SERVER_USER/nexus-core/venv/bin/python -m nexus.core.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=nexus-core

[Install]
WantedBy=multi-user.target
EOF

scp_copy "$TEMP_DIR/nexus-core.service" "$SERVER_USER@$SERVER_HOST:/tmp/nexus-core.service"
sudo_exec "mv /tmp/nexus-core.service /etc/systemd/system/nexus-core.service"
sudo_exec "systemctl daemon-reload"
sudo_exec "systemctl enable nexus-core"

echo "Starting Service..."
sudo_exec "systemctl restart nexus-core"

echo ""
echo "=== Deployment Complete! ==="
echo "Dashboard: http://$SERVER_HOST:8000"
