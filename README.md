# Nexus 🌐

**Distributed Debian Fleet Orchestration Platform**

> *Control your fleet from the command line. Deploy services with Docker.*

Nexus is a lightweight, secure, and modular platform for managing fleets of Debian-based machines (Raspberry Pi, Ubuntu, Debian servers). Built with a **CLI-First** and **Docker-First** philosophy, it provides robust headless management, monitoring, and service orchestration with an optional "Single Pane of Glass" web dashboard.

## 🚀 Core Philosophy

*   **CLI-First:** Every feature is built as a command-line tool first. Automation and scripting are first-class citizens.
*   **Docker-First:** Services are deployed and managed as Docker containers across your fleet. Consistent, reproducible deployments.
*   **Debian-Based:** Works on Raspberry Pi OS, Ubuntu, Debian, and any Debian-derivative Linux distribution.
*   **Decentralized:** Agents run locally on each node, handling monitoring and tasks independently.
*   **Network Agnostic:** Works on any local network out of the box. Optionally use ZeroTier/Tailscale for secure remote access.
*   **Modular:** Deploy services like Pi-hole, Home Assistant, Prometheus, or custom containers across your fleet.

## 🏗️ Architecture

> **See the full System Map:** [ARCHITECTURE.md](ARCHITECTURE.md)

```mermaid
graph TD
    User[User] -->|CLI / Web| Core[Nexus Core]
    Core -->|Local Network / VPN| Agent1[Agent: Kitchen]
    Core -->|Local Network / VPN| Agent2[Agent: Study]
    Core -->|Local Network / VPN| Agent3[Agent: Garage]

    subgraph "Nexus Core"
        DB[(SQLite)]
        API[FastAPI Server]
        CLI[CLI Tool]
    end

    subgraph "Agent Node"
        AgentAPI[FastAPI Agent]
        Monitor[Speculum (Metrics)]
        Terminal[Imperium (Shell)]
        Worker[Scriptor (Jobs)]
    end
```

## 🎯 Core Features

### ✅ Implemented

**Fleet Monitoring (Speculum)** - Real-time system health metrics
*   Collects CPU, RAM, Disk, Temperature every 30 seconds
*   **Multi-disk detection** - Automatically detects all physical disks, partitions, and mount points
    *   Smart primary storage identification (boot partitions, root filesystems, largest disk)
    *   Categorizes disks by type (HDD, SSD, NVMe, SD Card, USB, Network)
    *   Provides storage recommendations for optimal disk selection
*   Works on any Debian-based system (`psutil` + platform-specific sensors)
*   Raspberry Pi: `vcgencmd` for accurate GPU temperature
*   Debian/Ubuntu: `lm-sensors` fallback for CPU temperature
*   Health status calculation with configurable thresholds
*   Historical metrics with aggregated statistics (min/max/avg)
*   WebSocket real-time updates to dashboard

**Remote Control (Imperium)** - Centralized logging and job execution
*   Centralized log collection from all agents
*   Remote shell command execution via job system
*   WebSocket-based terminal infrastructure (server-side ready)
*   Job queue with concurrent execution limits
*   Result reporting and tracking

**Web Dashboard** - Real-time fleet monitoring (UniFi-style with purple theme)
*   Live metrics visualization (CPU, memory, disk, temperature)
*   Health status overview for all nodes
*   Log viewer with filtering and search
*   Job submission and monitoring UI
*   System topology and node discovery
*   WebSocket real-time updates (instant, no polling)
*   Unique CLI view showing equivalent commands for every action
*   📋 **See full UI/UX plan:** [`docs/plans/dashboard-ui-plan.md`](docs/plans/dashboard-ui-plan.md)



### 📦 Optional (Vigil Legacy - Parked)

**Scriptor (OCR Engine)** - Digitizes handwritten/printed notes
*   Infrastructure ready via job system
*   Would use Tesseract 4.x for OCR processing
*   Not required for core fleet management

**Arbiter (Sync Manager)** - Resolves Syncthing file conflicts
*   Infrastructure ready via job system
*   Would watch for `.stconflict` files
*   Not required for core fleet management

## 🛠️ Technology Stack

*   **Language:** Python 3.11+
*   **CLI:** [Typer](https://typer.tiangolo.com/) - *Fast, easy CLI building.*
*   **Web/API:** FastAPI - *Modern async framework with built-in OpenAPI docs and WebSocket support.*
*   **Database:** SQLite - *Single-file, easy backup.*
*   **Orchestration:** Docker & Docker Compose - *Container deployment and service management.*
*   **Networking:** Local network discovery with optional ZeroTier/Tailscale for remote access.
*   **Supported OS:** Raspberry Pi OS, Ubuntu, Debian, and derivatives (any Debian-based Linux)

## ⚡ Getting Started

### Prerequisites

**Control Node (Core Server):**
*   Python 3.11+
*   Docker & Docker Compose (optional, for Core deployment)
*   Local network (or VPN like ZeroTier/Tailscale for remote access)

**Managed Nodes (Agents):**
*   Debian-based Linux (Raspberry Pi OS, Ubuntu, Debian, etc.)
*   Python 3.11+
*   Docker & Docker Compose (for service orchestration)
*   SSH access (for automated deployment)
*   sshpass (for automated deployment from Core)

### Installation (Dev)

```bash
# Clone the repo
git clone https://github.com/yourusername/nexus.git
cd nexus

# Install dependencies in virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start the Core server
python -m nexus.core.main
# Visit http://localhost:8000 for dashboard
```

### Deploying to Managed Nodes (Debian-based)

```bash
# Deploy agent to any Debian-based machine (Raspberry Pi, Ubuntu, Debian)
./scripts/deploy-pi.sh <node_ip> <node_user> <node_password> <core_ip>

# Example - Raspberry Pi:
./scripts/deploy-pi.sh 10.243.14.179 pi raspberry 10.243.29.55

# Example - Ubuntu Server:
./scripts/deploy-pi.sh 192.168.1.100 ubuntu mypassword 192.168.1.10

# The script will:
# - Copy agent code to node
# - Install dependencies (Python, Docker if needed)
# - Configure agent to connect to Core
# - Start the agent service

# Check deployment
ssh user@node_ip "cd ~/nexus-agent && cat agent.log"
```

## 📖 Usage

Nexus is controlled primarily through the `nexus` command.

### Node Management
```bash
# List all connected nodes
nexus node list

# Get detailed status of a node
nexus node status <node_id>

# Open a remote shell
nexus node shell <node_id>
```

### Metrics & Health
```bash
# View recent metrics for a node
nexus metrics get <node_id>

# View aggregated statistics (min/max/avg)
nexus metrics stats <node_id>

# View health status with thresholds
nexus metrics health <node_id>
```

### Logs
```bash
# View logs from all nodes
nexus logs list

# View logs from a specific node
nexus logs list <node_id>

# Tail logs in real-time
nexus logs tail
```



### Job Management
```bash
# Submit an OCR job
nexus job submit --file document.jpg --node <node_id>

# Check job status
nexus job list
```

### System
```bash
# View system configuration
nexus config show

# Update all agents
nexus fleet update
```

## 🗺️ Roadmap

- [x] **Phase 1: The Bedrock** - Core Library & CLI foundation. ✅
- [x] **Phase 2: The Mesh** - Agent discovery & secure connectivity. ✅
- [x] **Phase 3: The Pulse** - Metrics collection & health monitoring. ✅
- [x] **Phase 4: The Brain** - Centralized logging & remote control. ✅
- [x] **Phase 5: The Hands** - Workload orchestration (Job execution system). ✅
- [x] **Phase 6.1: The Dashboard** - Live metrics visualization (Charts with Chart.js). ✅
- [x] **Pi Deployment** - First real Raspberry Pi deployment successful (moria-pi). ✅
- [x] **Phase 6.2: Node Detail View** - Comprehensive node management with real-time charts. ✅
- [x] **WebSocket Real-time Updates** - Instant updates replacing 30s polling. ✅
- [x] **Phase 6.3: Jobs Management UI** - Full job submission, monitoring, and review interface. ✅
- [x] **Modules Preview** - Stub page for future module deployment system (Phase 7). ✅
- [x] **Phase 6.4: Log Viewer UI** - Web-based log viewer with filtering and search. ✅
- [x] **Phase 6.5.1: Multi-Disk Detection** - Comprehensive disk detection and smart storage recommendations. ✅

- [x] **Phase 6.6: UI Polish & UX Improvements**
  - [x] Global Toast Notification System (replaces alerts)
  - [x] Loading states for buttons (refresh, submit)
  - [x] Consistent status badges and colors
  - [x] Improved empty states for lists
- [ ] **Phase 8: Fleet Management** - Centralized agent update and fleet-wide operations.
  - [ ] Remote agent code updates from web dashboard (one-click agent updates)
  - [ ] Remote agent code updates via CLI (`nexus fleet update`, `nexus node update <node_id>`)
  - [ ] Agent version tracking and update availability notifications
  - [ ] Fleet-wide configuration management
  - [ ] Bulk operations across multiple nodes (update all, restart all, etc.)
  - [ ] Update rollback mechanism for failed updates
  - [ ] Zero-downtime agent updates with graceful restarts

## 🔒 Security

*   **Shared Secret:** Pre-shared key authentication for new nodes.
*   **API Tokens:** Unique tokens issued to agents after registration.
*   **TLS/HTTPS:** All API communication encrypted with TLS certificates.
*   **VPN Optional:** For remote access, use encrypted VPN solutions like ZeroTier or Tailscale.

## ⚙️ Configuration

### Log Retention

Nexus automatically manages log retention to prevent disk space issues. Configure log retention in your `.env` file:

```bash
# Number of days to keep logs (0 = keep forever)
NEXUS_LOG_RETENTION_DAYS=7  # Default: 7 days

# How often to run cleanup (in hours)
NEXUS_LOG_CLEANUP_INTERVAL_HOURS=24  # Default: 24 hours
```

**How it works:**
- The Core server runs a background cleanup task that deletes logs older than the retention period
- Cleanup runs automatically on startup (after 1 minute) and then on the specified interval
- Set `NEXUS_LOG_RETENTION_DAYS=0` to keep logs forever (not recommended for production)
- Logs are deleted permanently from the database - ensure you have external backups if needed

**Recommendations:**
- **Development:** 7 days (default)
- **Production:** 30-90 days depending on fleet size and disk space
- **High-volume fleets:** 7-14 days with external log aggregation

---

## 📝 Documentation

All documentation is up-to-date and reflects the current implementation:
- **README.md** - Core features, CLI usage, and getting started guide
- **docs/api.md** - Complete REST API reference with all endpoints
- **docs/api.md** - Complete REST API reference with all endpoints
- **ARCHITECTURE.md** - System architecture including multi-disk detection and Docker orchestration
- **CONTRIBUTING.md** - Development guidelines and **error handling best practices**
- **PROGRESS.md** - Development progress and phase completion tracking

- **CONTEXT.md** - Project context and implementation details

---
*Built with ❤️ for the Raspberry Pi Community.*
