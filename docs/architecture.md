# Nexus Architecture

## Overview

Nexus is a distributed fleet orchestration platform for Debian-based machines, built with a **CLI-first** and **Docker-first** philosophy. The architecture consists of two main components: **Core** (control plane) and **Agent** (data plane), with Docker serving as the primary mechanism for deploying and managing services across the fleet.

**Supported Systems:** Raspberry Pi OS, Ubuntu, Debian, and any Debian-derivative Linux distribution.

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

The Agent runs on each managed node (Raspberry Pi, Ubuntu server, Debian machine, etc.).

**Responsibilities:**
- Register with Core on startup
- Execute jobs assigned by Core (shell commands, Docker operations)
- Collect and report system metrics (CPU, RAM, disk, temperature)
- Manage Docker containers and services
- Provide remote shell access (WebSocket-based)
- Monitor Docker container health and resource usage

**Technology:**
- FastAPI for agent API
- psutil for system metrics (cross-platform)
- Docker SDK for Python for container management
- Platform-specific monitoring (vcgencmd for Pi, lm-sensors for others)

**Deployment:**
- Runs as a systemd service on each node
- Python virtual environment for isolation
- Dockerized deployment optional (for Core compatibility)

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

## Docker Service Orchestration (Phase 7)

Nexus uses Docker as the foundational technology for deploying and managing services across the fleet.

### Architecture

```
┌──────────────┐
│  Nexus Core  │ ─── Service Template ─── Docker Compose YAML
└──────┬───────┘
       │
       │ Deploy Command (via API/CLI)
       │
       v
┌─────────────────┐
│  Agent Node     │
│  ┌───────────┐  │
│  │ Docker    │  │
│  │ Daemon    │  │
│  └─────┬─────┘  │
│        │        │
│  ┌─────v──────┐ │
│  │ Container  │ │
│  │ (Pi-hole)  │ │
│  └────────────┘ │
└─────────────────┘
```

### Service Lifecycle Management

**1. Service Templates**
- Pre-defined Docker Compose configurations for common services
- Templates for: Pi-hole, Home Assistant, Prometheus, Grafana, etc.
- Custom templates supported via YAML upload

**2. Deployment Process**
```
User → CLI/Web → Core API → Agent API → Docker SDK → Container Running
```

**3. Supported Operations**
- **deploy**: Pull image and start container
- **start/stop/restart**: Control running containers
- **update**: Pull new image version and restart
- **remove**: Stop and remove container
- **logs**: Stream container logs
- **inspect**: Get container status and configuration

**4. Health Monitoring**
- Container status (running, stopped, exited)
- Resource usage (CPU, memory per container)
- Docker daemon health
- Automatic restart policies

### Multi-Node Deployments

Services can be deployed to:
- Single node (e.g., Pi-hole on gateway Pi)
- Multiple nodes (e.g., distributed Prometheus exporters)
- All nodes (e.g., monitoring agents)

### Docker API Integration

**Agent-side:**
- Uses Docker SDK for Python (`docker-py`)
- Communicates with local Docker daemon via socket
- Translates Nexus commands to Docker API calls

**Core-side:**
- Stores service definitions and deployment state
- Tracks which services are running on which nodes
- Provides unified view of fleet-wide services

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

### Near-term (Phase 7)
- **Docker Orchestration:** Full Docker service deployment and management
- **Service Templates:** Pre-built configurations for common services
- **Container Monitoring:** Resource usage and health tracking per container
- **Docker Compose Support:** Multi-container application deployments

### Long-term
- **Service Discovery:** Implement mDNS for zero-config setup on local networks
- **HA Core:** Multiple Core replicas with leader election for reliability
- **Edge Intelligence:** Agents can execute jobs locally when Core is offline
- **Plugin System:** Dynamic module loading for custom workflows and integrations
- **Kubernetes Support:** Optional K8s orchestration for larger deployments
- **Container Registry:** Private Docker registry for custom images
