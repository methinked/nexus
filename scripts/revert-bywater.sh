#!/bin/bash
# Revert Script for Bywater-Pi
# Aborts migration and restores state to SD Card

set -e

echo "=== Bywater-Pi Revert to SD Card ==="

# 1. Stop Services
echo "[1/5] Stopping services..."
sudo systemctl stop docker
sudo systemctl stop nexus-agent || pkill -f 'python.*nexus.agent.main' || true

# 2. Restore Docker Config
echo "[2/5] Restoring Docker config..."
if [ -f "/etc/docker/daemon.json" ]; then
    # We remove the custom data-root to fallback to default (/var/lib/docker)
    sudo rm /etc/docker/daemon.json
    echo "    Removed custom daemon.json (reverted to default)."
fi

# 3. Restore Data Locations
echo "[3/5] Checking data locations..."

# Docker
if [ -d "/var/lib/docker.old" ]; then
    echo "    Restoring /var/lib/docker from backup..."
    sudo rm -rf /var/lib/docker 2>/dev/null || true
    sudo mv /var/lib/docker.old /var/lib/docker
elif [ -d "/var/lib/docker" ]; then
    echo "    /var/lib/docker exists. Using it."
else
    echo "WARNING: No Docker directory found in /var/lib. Docker will start fresh."
fi

# Agent
# Remove symlink if it exists
if [ -L "/home/methinked/nexus-agent" ]; then
    echo "    Removing Agent symlink..."
    sudo rm /home/methinked/nexus-agent
fi

# Restore .old if needed
if [ -d "/home/methinked/nexus-agent.old" ]; then
    echo "    Restoring agent from nexus-agent.old..."
    sudo mv /home/methinked/nexus-agent.old /home/methinked/nexus-agent
fi

# Fix permissions just in case
if [ -d "/home/methinked/nexus-agent" ]; then
    sudo chown -R methinked:methinked /home/methinked/nexus-agent
fi

# 4. Cleanup Fstab
echo "[4/5] Cleaning fstab..."
# remove any line with /mnt/data
sudo sed -i '/\/mnt\/data/d' /etc/fstab
sudo systemctl daemon-reload

# 5. Restart
echo "[5/5] Restarting services..."
sudo systemctl start docker

# Check Docker Root
ROOT_DIR=$(sudo docker info | grep "Docker Root Dir")
echo "    $ROOT_DIR"

if echo "$ROOT_DIR" | grep -q "/var/lib/docker"; then
    echo "    SUCCESS: Docker is back on SD Card."
else
    echo "    WARNING: Docker might still be pointing elsewhere."
fi

# Restart Agent
if systemctl list-unit-files | grep -q nexus-agent; then
     sudo systemctl start nexus-agent
else
     echo "Starting agent manually..."
     cd /home/methinked/nexus-agent
     nohup venv/bin/python -m nexus.agent.main > agent.log 2>&1 &
fi

echo "=== Revert Complete ==="
