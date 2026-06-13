# Moria-Pi Agent Deployment Guide

## Overview
This guide deploys the Nexus Agent to moria-pi (10.243.14.179) with proper configuration for external HDD storage.

**Status:** Moria-pi is currently unreachable (may still be booting or not on network yet)

## Prerequisites

- [ ] Moria-pi is online and reachable at 10.243.14.179
- [ ] SSH access available (user: `methinked`, password: `107512625`)
- [ ] External HDD is mounted at `/mnt/nexus-storage` (or custom path)
- [ ] Orthanc-pi (core server) is running at 10.243.151.228:8000
- [ ] Shared secret from `.env` file

## Deployment Steps

### 1. Wait for Moria-Pi to Come Online

If moria-pi is still booting, wait and then test connectivity:

```bash
# Test SSH connectivity
ssh methinked@10.243.14.179 "hostname"

# Or via ZeroTier (if configured)
ping 10.243.14.179
```

### 2. Prepare External HDD (On Moria-Pi)

SSH to moria-pi and set up the external storage:

```bash
# SSH to moria-pi
ssh methinked@10.243.14.179

# Check available block devices
lsblk

# Create mount point (if not already done)
sudo mkdir -p /mnt/nexus-storage

# If you need to mount the USB drive (example: /dev/sda1)
# sudo mount /dev/sda1 /mnt/nexus-storage
# Or make it persistent in /etc/fstab

# Verify mount
ls -la /mnt/nexus-storage
```

### 3. Run the Deployment Script

From the project root directory:

```bash
# With defaults (HDD at /mnt/nexus-storage)
cd ~/Projects/nexus/nexus
./scripts/deploy-moria-pi.sh

# Or with custom HDD mount path
./scripts/deploy-moria-pi.sh /mnt/custom-path

# Or with custom shared secret (if not in .env)
./scripts/deploy-moria-pi.sh /mnt/nexus-storage "your-secret-here"
```

### 4. Verify Deployment

After the script completes:

```bash
# Check agent status on moria-pi
ssh methinked@10.243.14.179 'systemctl status nexus-agent'

# Test health endpoint
curl http://10.243.14.179:8001/health

# Check logs on external HDD
ssh methinked@10.243.14.179 'ls -lah /mnt/nexus-storage/logs/'

# Follow logs in real-time
ssh methinked@10.243.14.179 'tail -f /mnt/nexus-storage/logs/*.log'

# Or via journalctl
ssh methinked@10.243.14.179 'journalctl -u nexus-agent -f'

# Verify registration on orthanc (core server)
curl http://10.243.151.228:8000/api/nodes?status=online
```

## Configuration Details

The deployment script creates:

**Environment File:** `/home/methinked/nexus-agent/.env`
```ini
NEXUS_NODE_NAME=moria-pi
NEXUS_CORE_URL=http://10.243.151.228:8000
NEXUS_AGENT_PORT=8001
NEXUS_LOGS_DIR=/mnt/nexus-storage/logs
NEXUS_DATA_DIR=/mnt/nexus-storage/data
NEXUS_ENV=production
```

**Service File:** `/etc/systemd/system/nexus-agent.service`
- Auto-restarts on failure
- Logs go to journalctl (and external HDD)
- Resource limits: 256MB RAM, 80% CPU (for Pi 3B+ stability)

## Troubleshooting

### Agent fails to start
```bash
# Check systemd service
ssh methinked@10.243.14.179 'systemctl status nexus-agent'

# View recent logs
ssh methinked@10.243.14.179 'journalctl -u nexus-agent -n 50'

# Try manual start
ssh methinked@10.243.14.179 'cd ~/nexus-agent && source venv/bin/activate && python -m nexus.agent.main'
```

### External HDD not available
```bash
# Check if mounted
ssh methinked@10.243.14.179 'df -h /mnt/nexus-storage'

# Mount it manually
ssh methinked@10.243.14.179 'sudo mount /dev/sda1 /mnt/nexus-storage'

# Or check dmesg for USB device
ssh methinked@10.243.14.179 'dmesg | tail -20 | grep -i usb'
```

### Agent not registering with orthanc
```bash
# Check connectivity to core server
ssh methinked@10.243.14.179 'curl -v http://10.243.151.228:8000/health'

# Verify network routing
ssh methinked@10.243.14.179 'ping 10.243.151.228'

# Check agent logs for auth errors
ssh methinked@10.243.14.179 'journalctl -u nexus-agent -g "register\|auth\|error" -n 20'

# For orthanc-pi specifically (dual core+agent role):
# Check if agent service is running
ssh methinked@10.243.151.228 'systemctl status nexus-agent'

# Check agent configuration for malformed URLs
ssh methinked@10.243.151.228 'grep CORE_URL ~/nexus-agent/.env'

# Fix common URL issue (double http:// prefix)
ssh methinked@10.243.151.228 'sed -i "s|NEXUS_CORE_URL=http://https://|NEXUS_CORE_URL=http://|g" ~/nexus-agent/.env'

# Restart agent service
ssh methinked@10.243.151.228 'sudo systemctl restart nexus-agent'
```

## File Locations

| Path | Purpose |
|------|---------|
| `~/nexus-agent/` | Agent installation directory |
| `~/nexus-agent/.env` | Agent configuration |
| `/mnt/nexus-storage/logs/` | Agent logs (NOT on SD card) |
| `/mnt/nexus-storage/data/` | Agent state files |
| `/etc/systemd/system/nexus-agent.service` | Systemd service file |
| `/var/log/syslog` | Systemd logs for the service |

## Important Notes

- **Logging:** All logs go to `/mnt/nexus-storage/logs/` on the external HDD, not the SD card
- **Data:** Agent state is stored on external HDD to avoid SD card wear
- **Performance:** Pi 3B+ is limited to 256MB RAM and 80% CPU to maintain stability
- **Restart:** Service auto-restarts with 10-second delay on failure
- **ZeroTier:** Agent communicates with core via 10.243.151.228 (ZeroTier IP of orthanc-pi)

---

**Related Scripts:**
- `deploy-pi.sh` - Generic Pi deployment template
- `deploy-moria-pi.sh` - Moria-specific deployment with HDD logging
- `update-agent.sh` - Update existing agent code
