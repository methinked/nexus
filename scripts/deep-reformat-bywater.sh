#!/bin/bash
# Deep Clean & Reformat Script for Bywater-Pi
# WARNING: DESTRUCTIVE - Wipes /dev/sda entirely

set -e

echo "=== Bywater-Pi Deep Clean & Reformat ==="
echo "Target: /dev/sda"
echo "Mode: ext4 (No Journaling)"

# 1. Unmount everything
echo "[1/6] Unmounting..."
sudo umount /mnt/data || true
sudo umount /dev/sda1 || true

# 2. Wipe Partition Table (Zap)
echo "[2/6] Wiping partition table..."
# Wipe start and end of disk to clear old GPT/MBR data
sudo wipefs --all --force /dev/sda
sudo dd if=/dev/zero of=/dev/sda bs=1M count=10 status=none

# 3. Create New Partition Table
echo "[3/6] Creating new GPT partition table..."
# Use parted to make a GPT table and a primary partition spanning 100%
sudo parted -s /dev/sda mklabel gpt
sudo parted -s /dev/sda mkpart primary ext4 0% 100%

# 4. Format to ext4 (No Journaling)
echo "[4/6] Formatting /dev/sda1 to ext4 (No Journal)..."
# -O ^has_journal disables the journal
# -F forces format
sudo mkfs.ext4 -F -O ^has_journal /dev/sda1

# 5. Connect & Mount
echo "[5/6] Updating /etc/fstab..."
NEW_UUID=$(sudo blkid -s UUID -o value /dev/sda1)
echo "    New UUID: $NEW_UUID"

if [ -z "$NEW_UUID" ]; then
    echo "ERROR: Could not get UUID. Format might have failed."
    exit 1
fi

# Backup fstab
sudo cp /etc/fstab /etc/fstab.backup.$(date +%s)

# Remove old entry
sudo sed -i '/\/mnt\/data/d' /etc/fstab

# Add new entry
# Added 'nofail' to prevent boot hang if drive fails
echo "UUID=$NEW_UUID /mnt/data ext4 defaults,auto,users,rw,nofail,noatime 0 0" | sudo tee -a /etc/fstab

# 6. Verify Mount
echo "[6/6] Mounting..."
sudo mkdir -p /mnt/data
sudo mount -a
echo "    Mount Status:"
df -hT /mnt/data

echo "=== Deep Clean Complete ==="
