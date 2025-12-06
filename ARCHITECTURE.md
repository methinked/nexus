# Nexus System Architecture 🏗️

> **The System Map**: A technical overview of how Nexus components fit together.

## 1. High-Level Topology

Nexus follows a **Hub-and-Spoke** architecture. The **Core** server acts as the central command post, while **Agents** run on managed nodes (Raspberry Pis, servers) to execute tasks and report data.

```mermaid
graph TD
    User((User))
    
    subgraph "Control Plane (Laptop/Server)"
        Core[Nexus Core]
        DB[(SQLite DB)]
        WebUI[Web Dashboard]
        CLI[Nexus CLI]
    end
    
    subgraph "Managed Fleet"
        Agent1[Agent: Moria-Pi]
        Agent2[Agent: Kitchen]
        Agent3[Agent: Garage]
    end

    User -->|HTTP/WebSocket| WebUI
    User -->|CLI Command| CLI
    CLI -->|REST API| Core
    WebUI -->|REST/WS| Core
    Core -->|Read/Write| DB
    
    Agent1 <-->|HTTP/WS| Core
    Agent2 <-->|HTTP/WS| Core
    Agent3 <-->|HTTP/WS| Core
```

---

## 2. Component Map

### 🧠 Nexus Core (`nexus/core/`)
The brain of the operation. Handles API requests, database storage, and fleet orchestration.
- **`main.py`**: Entry point. Sets up FastAPI, static files, and database connection.
- **`api/`**: REST endpoints for the Dashboard and Agents.
    - `nodes.py`: Node registration & management.
    - `metrics.py`: Metrics ingestion & history.
    - `jobs.py`: Job submission & status tracking.
- **`services/`**: Background logic.
    - `health.py`: Calculates node health status.
    - `logs.py`: Manages centralized logging.
- **`db/`**: SQLAlchemy models (`models.py`) and database access.

### 🤖 Nexus Agent (`nexus/agent/`)
The hands and eyes. Runs on every managed node.
- **`main.py`**: Entry point. Auto-registers with Core on startup.
- **`services/`**:
    - `metrics.py`: Collects system stats (CPU, Mem, Disk, Temp) every 30s. Uses `psutil` & `vcgencmd`.
    - `job_queue.py`: FIFO queue for executing tasks (shell commands, etc.).
    - `log_collector.py`: Buffers and sends logs to Core.
- **`api/`**: Local control endpoints (used by Core to command the Agent).

### 🖥️ Web Interface (`nexus/web/`)
The "Single Pane of Glass".
- **`templates/`**: Jinja2 HTML templates (`dashboard.html`, `nodes.html`).
- **`static/css/styles.css`**: Tailwind CSS + Custom "Cyber" theme styles.
- **`static/js/nexus-ui.js`**: **(Refactored)** Central page controller. Handles WebSocket connections and auto-refresh logic.
- **`static/js/nexus-charts.js`**: **(Refactored)** Centralized Chart.js configuration and multi-series update logic.

---

## 3. Data Flows

### 📊 Metric Pipeline (The "Pulse")
How data gets from a Raspberry Pi CPU to your browser chart.

```mermaid
sequenceDiagram
    participant HW as Hardware (Pi)
    participant Agent as Agent Service
    participant Core as Core Server
    participant DB as SQLite
    participant Browser as Web Dashboard

    loop Every 30s
        Agent->>HW: Read Sensors (psutil/vcgencmd)
        HW-->>Agent: CPU: 5%, Temp: 48°C
        Agent->>Core: POST /api/metrics (JSON)
        Core->>DB: INSERT into metrics_table
        
        par Real-time Update
            Core->>Browser: WebSocket 'metric_update' event
        end
    end

    Browser->>Core: GET /api/metrics (History)
    Core->>Browser: JSON Array
    Browser->>Browser: Chart.js Render
```

### ⚡ Control Flow (The "Hands")
How a job (e.g., "Run Update") is executed.

```mermaid
sequenceDiagram
    participant User
    participant Core
    participant Agent
    participant Shell as System Shell

    User->>Core: POST /api/jobs (cmd: "apt update")
    Core->>DB: Create Job (PENDING)
    Core->>Agent: POST /api/jobs/execute
    Agent->>Agent: Add to JobQueue
    Core-->>User: Job Created (ID: 123)

    loop Async Execution
        Agent->>Shell: Run Command
        Shell-->>Agent: Output ("Reading package lists...")
    end

    Agent->>Core: PATCH /api/jobs/123 (COMPLETED)
    Core->>DB: Update Job Status
    Core->>User: WebSocket 'job_update'
```

---

## 4. Key Configurations
- **Database**: `nexus.db` (SQLite) in `data/` directory.
- **Logs**: `nexus.log` in `logs/` directory.
- **Config**: Environment variables in `.env` (Source of Truth).
    - `NEXUS_CORE_URL`: Where Agents look for the Core.
    - `NEXUS_SHARED_SECRET`: Password for new Agents to join.
