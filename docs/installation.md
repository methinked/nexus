# Nexus Installation Guide

This guide covers installing Nexus Core (central server) and Nexus Agent (on Raspberry Pi nodes).

---

## Architecture

- **Core**: Central server that manages the fleet (runs on laptop/server)
- **Agent**: Lightweight service on each Raspberry Pi node
- **CLI**: Command-line tool (can run on Core server or separately)

---

## Prerequisites

### Core Server Requirements
- Python 3.11+ (tested with 3.13)
- Linux, macOS, or Windows
- At least 512MB RAM
- 1GB disk space for database

### Agent Requirements (Raspberry Pi)
- Raspberry Pi 3+ (ARMv7/v8)
- Python 3.11+
- Raspberry Pi OS (Debian-based)
- Network connectivity to Core server

---

## Installing Nexus Core (Central Server)

### 1. Clone the repository

```bash
git clone https://github.com/methinked/nexus.git
cd nexus
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Core dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

### 4. Configure Core

Create a `.env` file or set environment variables:

```bash
# Required
NEXUS_SHARED_SECRET=your-secret-here-change-in-production
NEXUS_JWT_SECRET_KEY=another-secret-change-in-production

# Optional (defaults shown)
NEXUS_CORE_HOST=0.0.0.0
NEXUS_CORE_PORT=8000
NEXUS_ENV=production
NEXUS_LOG_LEVEL=info
```

### 5. Initialize database

```bash
# Database will be created automatically on first run
# Or manually initialize:
python -c "from nexus.core.db import init_db; init_db()"
```

### 6. Start Core server

**Development:**
```bash
python -m nexus.core.main
```

**Production (with uvicorn):**
```bash
uvicorn nexus.core.main:app --host 0.0.0.0 --port 8000
```

**As a systemd service (Linux):**
```bash
# See docs/systemd/nexus-core.service
sudo cp docs/systemd/nexus-core.service /etc/systemd/system/
sudo systemctl enable nexus-core
sudo systemctl start nexus-core
```

### 7. Verify Core is running

```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","version":"0.1.0",...}
```

---

## Installing Nexus Agent (Raspberry Pi)

### Option 1: Manual Installation (Current Method)

#### 1. Copy Nexus to the Pi

```bash
# From your Core server:
scp -r nexus/ pi@raspberrypi.local:~/
```

Or clone directly on the Pi:
```bash
ssh pi@raspberrypi.local
git clone https://github.com/methinked/nexus.git
cd nexus
```

#### 2. Install Agent dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-agent.txt
pip install -e .
```

#### 3. Configure Agent

Create `.env` file on the Pi:

```bash
# Required - point to your Core server
NEXUS_CORE_URL=http://192.168.1.100:8000  # Your Core server IP
NEXUS_SHARED_SECRET=your-secret-here-change-in-production

# Optional
NEXUS_NODE_NAME=pi-bedroom  # Unique name for this node
NEXUS_AGENT_HOST=0.0.0.0
NEXUS_AGENT_PORT=8001
NEXUS_METRICS_INTERVAL=30  # Seconds between metrics
```

#### 4. Start Agent

**Development:**
```bash
python -m nexus.agent.main
```

**Production:**
```bash
uvicorn nexus.agent.main:app --host 0.0.0.0 --port 8001
```

**As a systemd service (recommended):**
```bash
# See docs/systemd/nexus-agent.service
sudo cp docs/systemd/nexus-agent.service /etc/systemd/system/
sudo systemctl enable nexus-agent
sudo systemctl start nexus-agent
```

#### 5. Verify Agent registered

On the Core server or any machine with the CLI:

```bash
nexus node list
# Should show your Pi with status "online"
```

---

## Installing Nexus CLI (Optional - separate machine)

If you want to manage your fleet from a different machine than Core:

```bash
git clone https://github.com/methinked/nexus.git
cd nexus
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .

# Configure CLI to point to Core
nexus config init
# Enter your Core server URL when prompted
```

---

## Quick Start with Docker (Future)

**Note:** Docker support is planned but not yet implemented.

```bash
# Core server
docker-compose up core

# Agent (on Pi)
docker run -d \
  -e NEXUS_CORE_URL=http://core-server:8000 \
  -e NEXUS_SHARED_SECRET=your-secret \
  --name nexus-agent \
  nexus/agent:latest
```

---

## Network Configuration

### Firewall Rules

**Core server:**
- Allow incoming TCP port 8000 from your local network

**Agent (Pi):**
- Allow incoming TCP port 8001 (only needed if Core calls Agent)
- Allow outgoing to Core port 8000

### Example: UFW (Ubuntu/Debian)

```bash
# On Core server
sudo ufw allow 8000/tcp

# On Agent (Pi) - optional
sudo ufw allow 8001/tcp
```

---

## Security Considerations

### 1. Change Default Secrets

**Critical:** Change both secrets before deploying:

```bash
# Generate secure secrets
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Set in `.env`:
```
NEXUS_SHARED_SECRET=<generated-secret-1>
NEXUS_JWT_SECRET_KEY=<generated-secret-2>
```

### 2. Local Network vs Internet

**Current design:** Nexus is designed for local network use.

For internet access:
- Use a VPN (ZeroTier, Tailscale, WireGuard)
- Or add TLS/SSL with reverse proxy (nginx, Caddy)
- Do NOT expose directly to internet without TLS

### 3. Agent State File

The agent stores `node_id` and `api_token` in `data/agent_state.json`:
- This file is sensitive - protect it
- If deleted, agent will re-register (may create duplicate)

---

## Troubleshooting

### Agent can't connect to Core

```bash
# Test connectivity from Pi
curl http://CORE_IP:8000/health

# Check Core is listening on 0.0.0.0, not 127.0.0.1
# In Core .env:
NEXUS_CORE_HOST=0.0.0.0
```

### Agent fails to register

- Check `NEXUS_SHARED_SECRET` matches between Core and Agent
- Check Core logs: `journalctl -u nexus-core -f`
- Check Agent logs: `journalctl -u nexus-agent -f`

### Metrics not appearing

```bash
# Check agent is submitting
journalctl -u nexus-agent | grep "HTTP Request: POST.*metrics"

# Check Core is receiving
journalctl -u nexus-core | grep "POST /api/metrics"

# Query database directly
sqlite3 data/nexus.db "SELECT COUNT(*) FROM metrics;"
```

---

## Uninstallation

### Remove Agent (Pi)

```bash
sudo systemctl stop nexus-agent
sudo systemctl disable nexus-agent
sudo rm /etc/systemd/system/nexus-agent.service
rm -rf ~/nexus
```

### Remove Core

```bash
sudo systemctl stop nexus-core
sudo systemctl disable nexus-core
sudo rm /etc/systemd/system/nexus-core.service
rm -rf ~/nexus
```

---

## Next Steps

1. **Configure CLI**: Run `nexus config init` to set up management
2. **Test commands**: Try `nexus node list`, `nexus node get <id>`
3. **Monitor metrics**: Check database for incoming metrics
4. **Submit jobs**: Use `nexus job submit` to test job orchestration

For more details, see:
- [Architecture Documentation](architecture.md)
- [API Reference](api.md)
- [CLI Guide](cli.md)
