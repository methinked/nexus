#!/bin/bash
# Script to backup the Nexus Core database from Moria-pi
# Usage: ./backup-moria.sh

set -e

CORE_IP="192.168.1.225"
USERNAME="methinked"
PASSWORD="107512625"
BACKUP_DIR="$(pwd)/data"
DATE=$(date +"%Y%m%d_%H%M%S")

echo "=== Backup Nexus Core from ${CORE_IP} ==="

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

if ! command -v sshpass &> /dev/null; then
    echo "Error: sshpass is not installed. Please run 'sudo apt install sshpass'"
    exit 1
fi

echo "[1/3] Backing up Nexus Database (SQLite)..."
# Create a compact backup using sqlite3 on the external drive, then compress and download
sshpass -p "${PASSWORD}" ssh -o StrictHostKeyChecking=no "${USERNAME}@${CORE_IP}" "sqlite3 /home/methinked/nexus-core/data/nexus.db '.backup /mnt/data/nexus_core_compact.db' || echo 'SQLite hit failing SD card sectors, salvaging what we can...'; tar -czvf /mnt/data/nexus_core_compact.db.tar.gz -C /mnt/data nexus_core_compact.db"
sshpass -p "${PASSWORD}" scp -o StrictHostKeyChecking=no "${USERNAME}@${CORE_IP}:/mnt/data/nexus_core_compact.db.tar.gz" "${BACKUP_DIR}/nexus_core_${DATE}.db.tar.gz"
sshpass -p "${PASSWORD}" ssh -o StrictHostKeyChecking=no "${USERNAME}@${CORE_IP}" "rm /mnt/data/nexus_core_compact.db /mnt/data/nexus_core_compact.db.tar.gz"

echo "[2/3] Backing up Environment Variables..."
sshpass -p "${PASSWORD}" scp -o StrictHostKeyChecking=no "${USERNAME}@${CORE_IP}:/home/methinked/nexus-core/.env" "${BACKUP_DIR}/nexus_core_${DATE}.env"

echo "[3/3] Backup Complete!"
echo "Files saved to: ${BACKUP_DIR}"
ls -lh "${BACKUP_DIR}/nexus_core_${DATE}.db"
