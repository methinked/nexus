#!/bin/bash
# Quick update script for already-deployed Nexus agents
# Usage: ./update-agent.sh <pi_host> <pi_user> <pi_password>

set -e

PI_HOST="${1:-10.243.14.179}"
PI_USER="${2:-methinked}"
PI_PASS="${3:-107512625}"

echo "=== Nexus Agent Update ==="
echo "Target: $PI_USER@$PI_HOST"
echo ""

# Helper function to run SSH commands
ssh_exec() {
    sshpass -p "$PI_PASS" ssh -o StrictHostKeyChecking=no "$PI_USER@$PI_HOST" "$@"
}

# Helper function to copy files
scp_copy() {
    sshpass -p "$PI_PASS" scp -o StrictHostKeyChecking=no -r "$@"
}

echo "[1/4] Stopping running agent..."
ssh_exec "pkill -f 'nexus.agent.main' || true"
sleep 2

echo "[2/4] Updating agent code..."
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Create deployment package with updated code
mkdir -p "$TEMP_DIR/nexus"
cp -r nexus/agent "$TEMP_DIR/nexus/"
cp -r nexus/shared "$TEMP_DIR/nexus/"
cp nexus/__init__.py "$TEMP_DIR/nexus/"

# Copy to Pi (preserving existing venv and config)
scp_copy "$TEMP_DIR/nexus" "$PI_USER@$PI_HOST:~/nexus-agent/"

echo "[3/4] Starting agent..."
ssh_exec "cd ~/nexus-agent && nohup ./start-agent.sh > agent.log 2>&1 &"
sleep 3

echo "[4/4] Checking agent status..."
HEALTH=$(curl -s "http://$PI_HOST:8001/health" 2>/dev/null || echo "FAILED")
if echo "$HEALTH" | grep -q "healthy"; then
    echo "✓ Agent is running and healthy!"
    curl -s "http://$PI_HOST:8001/" | python3 -m json.tool 2>/dev/null || true
else
    echo "✗ Agent may not be running. Check logs:"
    echo "  ssh $PI_USER@$PI_HOST 'tail ~/nexus-agent/agent.log'"
fi

echo ""
echo "=== Update Complete! ==="
echo ""
