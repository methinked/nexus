# Nexus 🌐

**Distributed Raspberry Pi Management System**

> *Control your fleet from the command line.*

Nexus is a lightweight, secure, and modular system for managing a fleet of Raspberry Pis. Built with a **CLI-First** philosophy, it provides robust headless management capabilities with an optional "Single Pane of Glass" web dashboard.

## 🚀 Core Philosophy

*   **CLI-First:** Every feature is built as a command-line tool first. Automation and scripting are first-class citizens.
*   **Decentralized:** Agents run locally on each node, handling monitoring and tasks independently.
*   **Secure Mesh:** Built on top of ZeroTier for secure, configuration-free networking.
*   **Modular:** Features like OCR, File Sync, and Monitoring are pluggable components.

## 🏗️ Architecture

```mermaid
graph TD
    User[User] -->|CLI / Web| Core[Nexus Core]
    Core -->|ZeroTier| Agent1[Agent: Kitchen]
    Core -->|ZeroTier| Agent2[Agent: Study]
    Core -->|ZeroTier| Agent3[Agent: Garage]
    
    subgraph "Nexus Core"
        DB[(SQLite)]
        API[API Server]
        CLI[CLI Tool]
    end
    
    subgraph "Agent Node"
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
    *   **Dev Note:** Port `modules.imperium` logic. Ensure Gunicorn/Uvicorn is configured for WebSockets (Eventlet/ASGI).

## 🛠️ Technology Stack

*   **Language:** Python 3.11+
*   **CLI:** [Typer](https://typer.tiangolo.com/) - *Fast, easy CLI building.*
*   **Web/API:** Flask (Core) + FastAPI (Agent)
*   **Database:** SQLite - *Single-file, easy backup.*
*   **Deployment:** Docker & Docker Compose

## ⚡ Getting Started

### Prerequisites
*   Python 3.11+
*   Docker & Docker Compose
*   ZeroTier Account

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

- [ ] **Phase 1: The Bedrock** - Core Library & CLI foundation.
- [ ] **Phase 2: The Mesh** - Agent discovery & secure connectivity.
- [ ] **Phase 3: The Pulse** - Metrics collection & Web Dashboard.
- [ ] **Phase 4: The Brain** - Centralized logging & remote control.
- [ ] **Phase 5: The Hands** - Workload orchestration (OCR, Sync).

## 🔒 Security

*   **Shared Secret:** Pre-shared key authentication for new nodes.
*   **API Tokens:** Unique tokens issued to agents after registration.
*   **Encrypted Transport:** All traffic flows over the ZeroTier encrypted mesh.

---
*Built with ❤️ for the Raspberry Pi Community.*
