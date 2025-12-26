#!/bin/bash
# Reformat Script for Bywater-Pi
# WARNING: DESTRUCTIVE - Formats /dev/sda1 to ext4

set -e

echo "=== Bywater-Pi Drive Reformat ==="
echo "Target: /dev/sda1"
echo "WARNING: All data on /dev/sda1 will be lost."

# 1. Unmount
echo "[1/4] Unmounting /mnt/data..."
sudo umount /mnt/data || true

# 2. Format to ext4
echo "[2/4] Formatting to ext4..."
# -F forces formatting
sudo mkfs.ext4 -F /dev/sda1

# 3. Update Fstab
echo "[3/4] Updating /etc/fstab..."
# Get new UUID
NEW_UUID=$(sudo blkid -s UUID -o value /dev/sda1)
echo "    New UUID: $NEW_UUID"

# Backup fstab
sudo cp /etc/fstab /etc/fstab.backup

# Remove old entry for /mnt/data (careful with sed)
sudo sed -i '/\/mnt\/data/d' /etc/fstab

# Add new entry
echo "UUID=$NEW_UUID /mnt/data ext4 defaults,auto,users,rw,nofail 0 0" | sudo tee -a /etc/fstab

# 4. Remount
echo "[4/4] Remounting..."
sudo mount -a
echo "    Mount success."
df -h /mnt/data

echo "=== Reformat Complete ==="
