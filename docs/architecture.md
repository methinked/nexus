# Nexus Architecture

## Overview

Nexus is a distributed system for managing Raspberry Pi nodes, built with a CLI-first philosophy. The architecture consists of two main components: **Core** and **Agent**.

## Components

### Core (Control Plane)

The Core is the central management server that orchestrates the fleet.

**Responsibilities:**
- Node registration and authentication
- Job scheduling and distribution
- Metrics aggregation and storage
- Web dashboard (optional)
- CLI command execution

**Technology:**
- FastAPI for REST API and WebSocket endpoints
- SQLite for persistent storage
- Typer for CLI

**Deployment:**
- Runs on a central server (can be a Raspberry Pi or any Linux machine)
- Accessible via local network or VPN

---

### Agent (Data Plane)

The Agent runs on each managed Raspberry Pi node.

**Responsibilities:**
- Register with Core on startup
- Execute jobs assigned by Core
- Collect and report system metrics
- Provide remote shell access
- Run modular workers (OCR, sync, etc.)

**Technology:**
- FastAPI for agent API
- psutil for system metrics
- Module-specific libraries (Tesseract, etc.)

**Deployment:**
- Runs as a systemd service on each Pi
- Dockerized for consistency

---

## Communication Flow

```
┌─────────────┐
│     User    │
└──────┬──────┘
       │ CLI / Web
       v
┌─────────────────┐
│   Nexus Core    │
│  (FastAPI App)  │
└────────┬────────┘
         │ HTTPS/WSS
         │ (Local Network / VPN)
         v
   ┌─────────────┐
   │    Agent    │
   │  (FastAPI)  │
   └──────┬──────┘
          │
     ┌────┴────┐
     v         v
[Modules]  [System]
```

---

## Authentication & Security

### Registration Flow

1. Agent starts with pre-configured **shared secret**
2. Agent sends registration request to Core (`POST /api/register`)
3. Core validates shared secret
4. Core issues unique **API token** to Agent
5. Agent stores token and uses for all future requests

### Request Authentication

- All API requests use Bearer token authentication
- Tokens are JWT-based with expiration
- Core validates tokens on each request

### Transport Security

- **Local Network:** TLS/HTTPS with self-signed or Let's Encrypt certs
- **Remote Access:** VPN layer (ZeroTier/Tailscale) provides encrypted tunnel

---

## Data Model

### Node

Represents a managed Raspberry Pi.

```python
{
    "id": "uuid",
    "name": "kitchen-pi",
    "ip_address": "192.168.1.100",
    "status": "online|offline|error",
    "last_seen": "timestamp",
    "metadata": {
        "location": "kitchen",
        "tags": ["camera", "ocr"]
    }
}
```

### Job

Represents a task to be executed on a node.

```python
{
    "id": "uuid",
    "type": "ocr|shell|sync",
    "node_id": "uuid",
    "status": "pending|running|completed|failed",
    "payload": {...},
    "created_at": "timestamp",
    "completed_at": "timestamp"
}
```

### Metric

System health metrics from a node.

```python
{
    "node_id": "uuid",
    "timestamp": "timestamp",
    "cpu_percent": 45.2,
    "memory_percent": 62.1,
    "disk_percent": 38.5,
    "temperature": 52.3
}
```

---

## Modules

### Speculum (Metrics Collection)

- Runs on Agent
- Collects CPU, RAM, disk, temperature every 30s
- Pushes metrics to Core via `POST /api/metrics`
- Core stores in SQLite for historical analysis

### Imperium (Remote Terminal)

- WebSocket-based remote shell
- User initiates from CLI: `nexus node shell <node_id>`
- Core proxies WebSocket to Agent
- Agent spawns PTY and streams I/O

### Scriptor (OCR Engine)

- Processes images submitted as jobs
- Uses Tesseract for text extraction
- Outputs Markdown files
- Syncs results back to Core via file sync

### Arbiter (Sync Conflict Resolver)

- Monitors Syncthing conflict files
- Reports conflicts to Core
- User resolves via CLI or Web UI

---

## Network Topology

### Local Network (Default)

```
┌──────────────────────────────────┐
│      Local Network (LAN)         │
│                                  │
│  ┌──────┐    ┌──────┐  ┌──────┐ │
│  │ Core │────│Agent1│──│Agent2│ │
│  └──────┘    └──────┘  └──────┘ │
│                                  │
└──────────────────────────────────┘
```

- Core listens on `0.0.0.0:8000`
- Agents discover Core via:
  - Manual configuration (IP in config file)
  - mDNS/Avahi broadcast (future)

### Remote Access (Optional)

```
┌────────────────────────────────────┐
│    Internet                        │
│                                    │
│  ┌──────┐    VPN Mesh    ┌──────┐ │
│  │ Core │◄──(ZeroTier)──►│Agent │ │
│  └──────┘                └──────┘ │
│                                    │
└────────────────────────────────────┘
```

- Install ZeroTier/Tailscale on Core and Agents
- Configure agents to use VPN IP for Core
- All traffic encrypted by VPN layer

---

## Deployment

### Development

```bash
# Run Core locally
uvicorn nexus.core.main:app --reload

# Run Agent locally
uvicorn nexus.agent.main:app --port 8001 --reload
```

### Production

**Core:**
```bash
docker-compose up -d nexus-core
```

**Agent (on each Pi):**
```bash
docker-compose up -d nexus-agent
```

Or use systemd service:
```bash
systemctl enable nexus-agent
systemctl start nexus-agent
```

---

## Scaling Considerations

### Core Scalability

- **SQLite Limits:** Good for ~100-500 nodes with moderate traffic
- **Migration Path:** If fleet grows, migrate to PostgreSQL
- **Horizontal Scaling:** Add Redis for job queue, use multiple Core replicas

### Agent Efficiency

- Lightweight metrics collection (minimal CPU/RAM)
- Job execution isolated in containers or processes
- Graceful degradation when Core unreachable

---

## Future Enhancements

- **Service Discovery:** Implement mDNS for zero-config setup
- **HA Core:** Multiple Core replicas with leader election
- **Edge Intelligence:** Agents can execute jobs locally when Core offline
- **Plugin System:** Dynamic module loading for custom workflows
