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

## 🧩 Component Migration (Vigil Legacy)

Nexus integrates the proven logic from the **Vigil** project into a distributed architecture.

### 1. Scriptor (OCR Engine) -> `nexus-worker-ocr`
*   **Purpose:** Digitizes handwritten/printed notes.
*   **Legacy Stack:** Tesseract 4.x, Pillow, File-based Queue.
*   **Nexus Implementation:**
    *   **Input:** Jobs submitted via CLI (`nexus job submit`) or Web.
    *   **Processing:** Background worker on Agent runs Tesseract.
    *   **Output:** Markdown files synced back to Core/Vault via Syncthing.
    *   **Dev Note:** Port `modules.scriptor.worker` logic. Ensure `tesseract-ocr` is in the Docker container.

### 2. Arbiter (Sync Manager) -> `nexus-sync`
*   **Purpose:** Resolves Syncthing file conflicts.
*   **Legacy Stack:** Python file scanner, `.stconflict` detection.
*   **Nexus Implementation:**
    *   **Monitoring:** Agent watches Syncthing folder for conflict files.
    *   **Resolution:** Reports conflicts to Core. User resolves via CLI (`nexus sync resolve <id>`) or Web.
    *   **Dev Note:** Port `modules.arbiter.conflict_scanner`. Needs read/write access to the Syncthing volume.

### 3. Speculum (System Monitor) -> `nexus-monitor`
*   **Purpose:** Real-time system health metrics.
*   **Legacy Stack:** `psutil`, `vcgencmd` (for Pi temp).
*   **Nexus Implementation:**
    *   **Collection:** Agent collects CPU, RAM, Disk, Temp every X seconds.
    *   **Transport:** Pushes lightweight JSON payload to Core API.
    *   **Dev Note:** Port `modules.speculum.metrics`. Abstract `vcgencmd` to handle non-Pi Linux systems gracefully.

### 4. Imperium (Remote Terminal) -> `nexus-terminal`
*   **Purpose:** Secure, web-based shell access.
*   **Legacy Stack:** Flask-SocketIO, `eventlet`.
*   **Nexus Implementation:**
    *   **Connection:** WebSocket tunnel initiated by CLI/Web to Core, proxied to Agent.
    *   **Security:** Authenticated via API Token.
    *   **Dev Note:** Port `modules.imperium` logic. FastAPI's native WebSocket support eliminates need for eventlet/socketio. Use Uvicorn for deployment.

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
*   Docker & Docker Compose
*   Local network (or VPN like ZeroTier/Tailscale for remote access)

### Installation (Dev)

```bash
# Clone the repo
git clone https://github.com/yourusername/nexus.git
cd nexus

# Install dependencies
pip install -r requirements.txt

# Initialize the Core
nexus config init
nexus db migrate
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
- [ ] **Phase 5: The Hands** - Workload orchestration (OCR, Sync).

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
