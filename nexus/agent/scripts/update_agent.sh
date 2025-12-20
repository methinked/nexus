#!/bin/bash
# Nexus Agent Self-Update Script
# Usage: ./update_agent.sh [branch]

set -e

# Auto-detect branch if not provided
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
BRANCH="${1:-$CURRENT_BRANCH}"
if [ -z "$BRANCH" ]; then
    BRANCH="dev"
fi
AGENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "=== Nexus Agent Update ==="
echo "Directory: $AGENT_DIR"
echo "Branch: $BRANCH"

cd "$AGENT_DIR"

# 1. Pull latest code
echo "[1/3] Pulling latest code..."
git fetch origin
git reset --hard "origin/$BRANCH"

# 2. Update dependencies
echo "[2/3] Updating dependencies..."
source venv/bin/activate
pip install -r requirements-agent.txt

# 3. Restart Service
echo "[3/3] Restarting service..."
# We use sudo here. Ensure the user has passwordless sudo for systemctl restart nexus-agent
# OR this script is run as root (unlikely for the agent process).
if command -v systemctl >/dev/null; then
    sudo systemctl restart nexus-agent
else
    echo "Error: systemctl not found. Cannot restart service."
    exit 1
fi
