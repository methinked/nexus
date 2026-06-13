# Moria-Pi Deployment Summary

**Date:** March 12, 2026  
**Status:** Ready for deployment (waiting for device to come online)  
**Target:** Moria-Pi (10.243.14.179) - Pi 3B+ with external HDD  
**Core Server:** Orthanc-Pi (10.243.151.228)

---

## What's Been Prepared

### 1. **Deployment Scripts**

#### `scripts/deploy-moria-pi.sh`
Custom deployment script for moria-pi with external HDD logging support.

**Features:**
- ✅ Configures logs to external HDD `/mnt/nexus-storage/logs` (not SD card)
- ✅ Configures data to external HDD `/mnt/nexus-storage/data`
- ✅ Checks external HDD availability and reports disk space
- ✅ Configures proper systemd service with resource limits for Pi 3B+
- ✅ Auto-restarts on failure
- ✅ Security hardening (ProtectSystem, MemoryLimit, CPUQuota)
- ✅ Full step-by-step progress reporting

#### `scripts/wait-and-deploy-moria.sh`
Helper script that waits for moria-pi to come online, then automatically runs the deployment.

**Usage:**
```bash
./scripts/wait-and-deploy-moria.sh [HDD_path] [max_retries] [retry_interval_seconds]

# Default: waits up to 5 minutes (60 retries × 5 seconds each)
./scripts/wait-and-deploy-moria.sh

# Custom: wait 10 minutes for HDD at /media/usb-storage
./scripts/wait-and-deploy-moria.sh /media/usb-storage 120 5
```

### 2. **Documentation**

#### `docs/deployment/moria-pi-deployment.md`
Complete deployment guide including:
- Prerequisites
- Step-by-step deployment instructions
- Post-deployment verification
- Configuration details
- Troubleshooting guide
- File locations reference

---

## Deployment Configuration

### Agent Configuration
- **Node Name:** `moria-pi`
- **Core Server:** `http://10.243.151.228:8000` (Orthanc-Pi)
- **Agent Port:** `8001`
- **Logs Directory:** `/mnt/nexus-storage/logs` (External HDD)
- **Data Directory:** `/mnt/nexus-storage/data` (External HDD)
- **Environment:** `production`

### Resource Limits (Pi 3B+ safety)
- **Memory:** 256MB RAM limit
- **CPU:** 80% quota (prevents system freeze)
- **Restart:** Auto-restart with 10-second delay on failure

### Log Storage
- **Physical Location:** External USB HDD at `/mnt/nexus-storage/logs`
- **NOT on SD card:** Prevents SD card wear and corruption
- **Systemd Integration:** Logs also available via `journalctl`

---

## How to Deploy

### Option 1: Automatic (Recommended - Device might still be booting)
```bash
cd ~/Projects/nexus/nexus
./scripts/wait-and-deploy-moria.sh /mnt/nexus-storage
```
This will wait for moria-pi to come online, then automatically run the full deployment.

### Option 2: Manual (Device is already online)
```bash
cd ~/Projects/nexus/nexus
./scripts/deploy-moria-pi.sh /mnt/nexus-storage
```

### Option 3: Custom HDD Path
If the external HDD is mounted elsewhere:
```bash
./scripts/deploy-moria-pi.sh /media/usb-storage
```

---

## Pre-Deployment Checklist

Before running deployment, ensure:

- [ ] Moria-pi is online and reachable at `10.243.14.179`
- [ ] External HDD is connected to moria-pi
- [ ] External HDD is mounted at `/mnt/nexus-storage` (or note the actual path)
- [ ] ZeroTier connectivity works: `ping 10.243.14.179`
- [ ] Orthanc-pi (core) is running: `curl http://10.243.151.228:8000/health`
- [ ] Shared secret available in `.env` file
- [ ] `sshpass` is installed locally: `which sshpass`

### Check Prerequisites
```bash
# Is orthanc running?
curl http://10.243.151.228:8000/health

# Is moria-pi reachable?
ping -c 1 10.243.14.179

# Do we have sshpass?
which sshpass || echo "Install: sudo apt-get install sshpass"

# Is shared secret in .env?
grep SHARED_SECRET ~/Projects/nexus/nexus/.env
```

---

## Post-Deployment Verification

After deployment completes, verify:

### 1. Service Status
```bash
ssh methinked@10.243.14.179 'systemctl status nexus-agent'
```

### 2. Health Check
```bash
curl http://10.243.14.179:8001/health
```

### 3. Log Files on HDD
```bash
ssh methinked@10.243.14.179 'ls -lah /mnt/nexus-storage/logs/'
```

### 4. Real-time Logs
```bash
# Option A: From external HDD
ssh methinked@10.243.14.179 'tail -f /mnt/nexus-storage/logs/*.log'

# Option B: From systemd journal
ssh methinked@10.243.14.179 'journalctl -u nexus-agent -f'
```

### 5. Registration on Core
```bash
# List all nodes on orthanc
curl http://10.243.151.228:8000/api/nodes

# Filter online nodes
curl 'http://10.243.151.228:8000/api/nodes?status=online'
```

---

## Key Files Created/Modified

| File | Purpose |
|------|---------|
| `scripts/deploy-moria-pi.sh` | Primary deployment script for moria-pi |
| `scripts/wait-and-deploy-moria.sh` | Auto-retry wrapper for deployment |
| `docs/deployment/moria-pi-deployment.md` | Full deployment guide |

---

## Troubleshooting

### Moria-Pi won't connect
- Check if device is powered on and has network cable
- Verify ZeroTier is routing: `ping 10.243.14.179`
- SSH manually to test: `ssh methinked@10.243.14.179`

### External HDD not found
- SSH to moria-pi and check mount: `lsblk`
- Verify HDD is USB-connected
- Check dmesg for device: `dmesg | grep -i usb | tail -10`

### Agent won't start
- Check service logs: `journalctl -u nexus-agent -n 50`
- Verify Python venv: `ssh methinked@10.243.14.179 'ls -la ~/nexus-agent/venv/bin/python'`
- Test manual start: `cd ~/nexus-agent && source venv/bin/activate && python -m nexus.agent.main`

### Agent can't reach core
- Test core connectivity: `curl http://10.243.151.228:8000/health`
- Check network routing: `ssh methinked@10.243.14.179 'route -n'`
- Verify firewall: Core should allow port 8000 from moria-pi

---

## Network Diagram

```
┌─────────────────────────────────────────────────────────┐
│ ZeroTier Network (10.243.x.x)                           │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Orthanc-Pi                    Moria-Pi                  │
│  10.243.151.228                10.243.14.179             │
│  192.168.1.222                 192.168.1.225             │
│  ┌──────────────────────┐      ┌─────────────────────┐  │
│  │ Core Server :8000    │      │ Agent :8001         │  │
│  │ Pi 5 + NVMe SSD      │◄─────│ Pi 3B+ + USB HDD    │  │
│  └──────────────────────┘      │                     │  │
│     Logs: Local                 │ Logs: /mnt/ext/    │  │
│     Data: Local DB              │ Data: /mnt/ext/    │  │
│                                 └─────────────────────┘  │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## Next Steps After Deployment

1. ✅ Agent deployed to moria-pi
2. ⬜ Verify registration on core
3. ⬜ Run system health check dashboard
4. ⬜ Consider deploying a test service (e.g., Pi-hole)
5. ⬜ Monitor logs for errors/warnings

---

**Questions?** See `docs/deployment/moria-pi-deployment.md` for detailed guide.
