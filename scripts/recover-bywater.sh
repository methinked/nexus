#!/bin/bash
# Recovery and Migration Script for Bywater-Pi
# 1. Reformats /dev/sda1 (Standard Journaled ext4)
# 2. Migrates data from backups (.old) to new drive
# 3. Restores services

set -e

echo "=== Bywater-Pi Recovery & Migration ==="

# 1. Stop Services
echo "[1/7] Ensuring services are stopped..."
sudo systemctl stop docker
sudo systemctl stop nexus-agent || pkill -f 'python.*nexus.agent.main' || true

# 2. Reformat Drive
echo "[2/7] Reformatting /dev/sda1 (Standard ext4 with Journal)..."
sudo umount /mnt/data || true
# Standard ext4 format (with journal by default)
sudo mkfs.ext4 -F /dev/sda1

# 3. Update Fstab
echo "[3/7] Updating fstab..."
NEW_UUID=$(sudo blkid -s UUID -o value /dev/sda1)
echo "    New UUID: $NEW_UUID"

if [ -z "$NEW_UUID" ]; then
    echo "ERROR: UUID not found. Format failed?"
    exit 1
fi

# Backup existing
sudo cp /etc/fstab /etc/fstab.backup.$(date +%s)
# Remove old /mnt/data line
sudo sed -i '/\/mnt\/data/d' /etc/fstab
# Add new line
echo "UUID=$NEW_UUID /mnt/data ext4 defaults,auto,users,rw,nofail 0 0" | sudo tee -a /etc/fstab

# 4. Mount
echo "[4/7] Mounting..."
sudo mkdir -p /mnt/data
sudo mount -a
df -h /mnt/data

# 5. Migrate Docker
echo "[5/7] Migrating Docker..."
sudo mkdir -p /mnt/data/docker
# Check where the source is
if [ -d "/var/lib/docker.old" ]; then
    echo "    Source: /var/lib/docker.old"
    sudo rsync -a /var/lib/docker.old/ /mnt/data/docker/
elif [ -d "/var/lib/docker" ]; then
    echo "    Source: /var/lib/docker"
    sudo rsync -a /var/lib/docker/ /mnt/data/docker/
    sudo mv /var/lib/docker /var/lib/docker.old
else
    echo "ERROR: Could not find Docker source directory!"
    exit 1
fi

# Configure Docker Daemon
echo '{"data-root": "/mnt/data/docker"}' | sudo tee /etc/docker/daemon.json

# 6. Migrate Agent
echo "[6/7] Migrating Agent..."
sudo mkdir -p /mnt/data/nexus-agent
# Fix Symlink mess from previous run
if [ -L "/home/methinked/nexus-agent" ]; then
    echo "    Removing old symlink..."
    sudo rm /home/methinked/nexus-agent
fi

# Check source
if [ -d "/home/methinked/nexus-agent.old" ]; then
    echo "    Source: nexus-agent.old"
    sudo cp -r /home/methinked/nexus-agent.old/* /mnt/data/nexus-agent/
    # We keep .old as backup
elif [ -d "/home/methinked/nexus-agent" ]; then
     # Use current if it exists (and wasn't the symlink)
     echo "    Source: nexus-agent"
     sudo cp -r /home/methinked/nexus-agent/* /mnt/data/nexus-agent/
     sudo mv /home/methinked/nexus-agent /home/methinked/nexus-agent.old
fi

# Create new Symlink
echo "    Linking..."
sudo ln -s /mnt/data/nexus-agent /home/methinked/nexus-agent
sudo chown -R methinked:methinked /mnt/data/nexus-agent
sudo chown -h methinked:methinked /home/methinked/nexus-agent

# 7. Restart
echo "[7/7] Restarting..."
sudo systemctl start docker

# Restart agent
if systemctl list-unit-files | grep -q nexus-agent; then
     sudo systemctl start nexus-agent
else
     echo "Starting agent manually..."
     cd /home/methinked/nexus-agent
     nohup venv/bin/python -m nexus.agent.main > agent.log 2>&1 &
fi

echo "=== Recovery Complete ==="
sudo docker info | grep "Docker Root Dir"
