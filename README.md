# Nexus 🌐

**Distributed Raspberry Pi Management System**

> *Control your fleet from the command line.*

Nexus is a lightweight, secure, and modular system for managing a fleet of Raspberry Pis. Built with a **CLI-First** philosophy, it provides robust headless management capabilities with an optional "Single Pane of Glass" web dashboard.

## 🚀 Core Philosophy

*   **CLI-First:** Every feature is built as a command-line tool first. Automation and scripting are first-class citizens.
*   **Decentralized:** Agents run locally on each node, handling monitoring and tasks independently.
*   **Network Agnostic:** Works on any local network out of the box. Optionally use ZeroTier for secure remote access.
*   **Modular:** Features like OCR, File Sync, and Monitoring are pluggable components.

## 🏗️ Architecture

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

**Speculum (System Monitor)** - Real-time system health metrics
*   Collects CPU, RAM, Disk, Temperature every 30 seconds
*   Uses `psutil` and `vcgencmd` (for Pi temp)
*   Pushes lightweight JSON payload to Core API
*   Health status calculation with configurable thresholds
*   Historical metrics with aggregated statistics

**Imperium (Remote Control)** - Centralized logging and job execution
*   Centralized log collection from all agents
*   Remote shell command execution via job system
*   WebSocket-based terminal infrastructure (server-side ready)
*   Job queue with concurrent execution limits
*   Result reporting and tracking

### 🚀 Planned (In Design)

**Web Dashboard** - Real-time fleet monitoring (UniFi-style with purple theme)
*   Live metrics visualization (CPU, memory, disk, temperature)
*   Health status overview for all nodes
*   Log viewer with filtering and search
*   Job submission and monitoring UI
*   System topology and node discovery
*   📋 **See full UI/UX plan:** [`docs/dashboard-ui-plan.md`](docs/dashboard-ui-plan.md)

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
*   **Deployment:** Docker & Docker Compose
*   **Networking:** Local network discovery with optional ZeroTier/Tailscale for remote access.

## ⚡ Getting Started

### Prerequisites
*   Python 3.11+
*   Docker & Docker Compose (optional)
*   Local network (or VPN like ZeroTier/Tailscale for remote access)
*   sshpass (for automated Pi deployment)

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

### Deploying to Raspberry Pi

```bash
# Deploy agent to a Raspberry Pi (automated)
./scripts/deploy-pi.sh <pi_ip> <pi_user> <pi_password> <core_ip>

# Example:
./scripts/deploy-pi.sh 10.243.14.179 methinked mypassword 10.243.29.55

# The script will:
# - Copy agent code to Pi
# - Install dependencies
# - Configure agent to connect to Core
# - Start the agent service

# Check deployment
ssh user@pi_ip "cd ~/nexus-agent && cat agent.log"
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

### Job Management
```bash
# Submit an OCR job
nexus job submit --file document.jpg --node <node_id>

# Check job status
nexus job list
```

### System
```bash
# View centralized logs
nexus logs --follow

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
- [x] **Modules Preview** - Stub page for future module deployment system (Phase 7). ✅

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
*Built with ❤️ for the Raspberry Pi Community.*
