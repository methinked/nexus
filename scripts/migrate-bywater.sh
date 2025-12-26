#!/bin/bash
# Migration Script for Bywater-Pi
# Moves Docker and Agent to /mnt/data (HDD)

set -e

echo "=== Bywater-Pi Storage Migration ==="
echo "Target: /mnt/data (HDD)"

# 1. Stop Services
echo "[1/6] Stopping services..."
sudo systemctl stop docker
sudo systemctl stop nexus-agent || pkill -f 'python.*nexus.agent.main' || true

# 2. Migrate Docker
echo "[2/6] Migrating Docker data (this may take a while)..."
if [ ! -d "/mnt/data/docker" ]; then
    sudo mkdir -p /mnt/data/docker
    sudo rsync -a /var/lib/docker/ /mnt/data/docker/
    echo "    Docker data synced."
else
    echo "    Target /mnt/data/docker already exists. Syncing updates..."
    sudo rsync -a /var/lib/docker/ /mnt/data/docker/
fi

# 3. Configure Docker
echo "[3/6] Configuring Docker daemon..."
if [ ! -f /etc/docker/daemon.json ]; then
    echo '{"data-root": "/mnt/data/docker"}' | sudo tee /etc/docker/daemon.json
else
    # Backup existing config
    sudo cp /etc/docker/daemon.json /etc/docker/daemon.json.bak
    # Check if 'data-root' exists using grep (simple check)
    if grep -q "data-root" /etc/docker/daemon.json; then
        sudo sed -i 's|"/var/lib/docker"|"/mnt/data/docker"|g' /etc/docker/daemon.json
    else
        # Append logic is complex in shell, overwriting if simple JSON, else manual intervention needed
        # Assuming simple config or empty
        echo '{"data-root": "/mnt/data/docker"}' | sudo tee /etc/docker/daemon.json
    fi
fi

# 4. Backup Old Docker Data
echo "[4/6] Backing up old Docker data..."
if [ -d "/var/lib/docker" ]; then
    sudo mv /var/lib/docker /var/lib/docker.old
fi

# 5. Migrate Agent
echo "[5/6] Migrating Nexus Agent..."
if [ -d "/home/methinked/nexus-agent" ]; then
    sudo mkdir -p /mnt/data/nexus-agent
    # Move current agent to HDD
    if [ ! -L "/home/methinked/nexus-agent" ]; then
        sudo cp -r /home/methinked/nexus-agent/* /mnt/data/nexus-agent/
        sudo mv /home/methinked/nexus-agent /home/methinked/nexus-agent.old
        # Create Symlink
        sudo ln -s /mnt/data/nexus-agent /home/methinked/nexus-agent
        echo "    Agent moved and symlinked."
    else
        echo "    Agent already appears to be specific link/moved."
    fi
    # Fix permissions
    sudo chown -R methinked:methinked /mnt/data/nexus-agent
fi

# 6. Restart Services
echo "[6/6] Restarting services..."
sudo systemctl start docker
# Restart Agent via systemd or manual (assuming systemd for robustness)
if systemctl list-unit-files | grep -q nexus-agent; then
    sudo systemctl start nexus-agent
else
    # Manual start fallback
    cd /home/methinked/nexus-agent
    nohup venv/bin/python -m nexus.agent.main > agent.log 2>&1 &
fi

echo "=== Migration Complete ==="
echo "Verifying Docker Root:"
sudo docker info | grep "Docker Root Dir"
