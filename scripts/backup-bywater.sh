#!/bin/bash
# Nightly Backup Script for Bywater-Pi
# Target: Orthanc-Pi (192.168.1.222)
# Storage: NVMe SSD

# Config
TARGET_HOST="192.168.1.222"
TARGET_USER="methinked"
TARGET_DIR="/home/methinked/backups/bywater-pi"
BACKUP_DATE=$(date +%Y-%m-%d)
LOG_FILE="/home/methinked/nexus-agent/logs/backup.log"

echo "[$(date)] Starting Backup to $TARGET_HOST..." >> $LOG_FILE

# 1. Ensure target directory exists
ssh $TARGET_USER@$TARGET_HOST "mkdir -p $TARGET_DIR"

# 2. Backup Docker Volumes (config/data)
# We assume standard locations. Adjust if using custom binds.
# Using sudo for read access, sending to user-owned destination.
# Note: rsync needs sudo on source to read docker files.
# For simplicity in this stop-gap, we back up the Nexus Agent data which contains state.
# For Docker volumes, we might need to stop containers or use `docker cp`.
# Let's focus on Nexus Data first as it's the "Brain" state.

echo "  Backing up Nexus Agent Data..." >> $LOG_FILE
rsync -avz -e ssh --delete \
    /home/methinked/nexus-agent/data \
    /home/methinked/nexus-agent/logs \
    $TARGET_USER@$TARGET_HOST:$TARGET_DIR/agent/ \
    >> $LOG_FILE 2>&1

# 3. Backup Critical Docker Binds (if any known)
# (Add specific paths here if needed, e.g., /opt/scriba/data)

if [ $? -eq 0 ]; then
    echo "[$(date)] Backup Successful" >> $LOG_FILE
    # Trigger a toast or log via API (Optional future step)
else
    echo "[$(date)] Backup FAILED" >> $LOG_FILE
fi
