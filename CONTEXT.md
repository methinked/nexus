## 1. Project Philosophy
**"Lightweight Fleet Management & Observability"**
Nexus is a focused, agent-based system for monitoring and managing home lab fleets (specifically Raspberry Pi nodes).

**Core Focus:** "Visibility & Control, without the bloat."

We sit in the "Goldilocks Zone" between:
- **Too Simple:** A static dashboard that just shows CPU usage. #Boring
- **Too Complex:** Kubernetes, K3s, or Ansible Tower. #Overkill

**What we ARE:**
- **Observer:** A "Single Pane of Glass" for fleet health (CPU, RAM, Temps, Storage).
- **Controller:** A standardized way to deploy Docker services (Pi-hole, Home Assistant) to specific nodes.
- **Automator:** A mechanism to run shell jobs and maintenance tasks.

**What we are NOT:**
- **Kubernetes:** We do not do "scheduling", "bin-packing", or "self-healing mesh networking". If a node dies, we alert you. We don't magically move workloads.
- **Terraform:** We manage *services*, not low-level infrastructure provisioning.

## 🚫 The "Anti-Creep" Manifesto (Guiding Principles)
*To keep this project maintainable and stable, we strictly adhere to these rules. If you (the User) or I (the AI) suggest breaking them, politely point to this section and say "No".*

1.  **Orchestration Lite:** Docker Compose is the source of truth. We do not invent our own container format. We just automate `docker compose up`.
2.  **No Complex Networking:** We assume a flat LAN (or VPN like ZeroTier). We DO NOT implement overlays, ingress controllers, or mesh routing.
3.  **Database Stability:** If a feature requires a complex migration that risks existing data for a "nice to have," it is rejected.
4.  **CLI First, Always:** If we can't do it in the terminal, it doesn't go in the UI.
5.  **Specific vs Generic:** We build headers for *our* specific use cases (Pi-hole, Home Assistant), not a generic "run anything anywhere" platform.
6.  **No "Smart" Scheduling:** Users pick which node runs a service. The system definitely does not pick.

**Documentation & Planning:**
- **Documentation is Key:** Update `README.md`, `CONTEXT.md`, and `docs/` frequently.
- **Careful Planning:** Document plans before execution.
- **Record Test Results:** Save major test outputs to `docs/tests/`.

**Target Hardware & Test Fleet:**
- Development: Linux laptop (x86_64)
- Production: Raspberry Pi (ARMv7/v8), Ubuntu servers (x86_64/ARM), Debian machines
- **Test Fleet:** 
  - **Orthanc-pi**: Primary Core Server & Agent. Connected via ZeroTier & LAN.
  - **Bywater-pi** (10.243.151.228): Remote Agent. Previously impacted by HDD failure.
  - **Moria-pi** (192.168.1.225): Offline. Raspberry Pi 3 Model B (ARMv7/v8, 1GB RAM) - SD Card Failure.

---

## ✅ What's Been Completed

### Phase 0: Project Initialization (Complete ✓)
- Full project structure created
- README.md updated with architectural decisions
- Docker configuration (docker-compose.yml, Dockerfiles)
- Comprehensive documentation (docs/architecture.md, docs/api.md)
- Development tooling (scripts/dev-setup.sh, .env.example)
- Git repository initialized with main and dev branches

### Phase 1: The Bedrock (Complete ✓)

#### 1. Shared Models ✓
**Location:** `nexus/shared/`

- `models.py`: Complete Pydantic models for all entities
  - Node, Job, Metric models with validation
  - Enums: NodeStatus, JobType, JobStatus
  - Auth models: Token, TokenData, Registration
  - System models: HealthResponse, SystemInfo, ErrorResponse

- `config.py`: Environment-based configuration
  - CoreConfig, AgentConfig, CLIConfig
  - Uses pydantic-settings with NEXUS_ prefix
  - Auto-creates data/logs directories

- `auth.py`: Authentication utilities
  - JWT token creation/verification
  - Shared secret validation
  - Password hashing with bcrypt
  - Custom exceptions: TokenExpiredError, TokenInvalidError

#### 2. Core FastAPI ✓
**Location:** `nexus/core/`

- `main.py`: Main FastAPI application
  - Lifespan management
  - CORS middleware
  - Health endpoint at `/health`
  - Router integration

- `api/auth.py`: Authentication endpoints
  - `POST /api/auth/register` - Node registration
  - `POST /api/auth/token/refresh` - Token refresh (stub)

- `api/nodes.py`: Node management
  - `GET /api/nodes` - List with filtering
  - `GET /api/nodes/{id}` - Get details
  - `PUT /api/nodes/{id}` - Update
  - `DELETE /api/nodes/{id}` - Deregister

- `api/jobs.py`: Job management
  - `POST /api/jobs` - Create job
  - `GET /api/jobs` - List with filtering
  - `GET /api/jobs/{id}` - Get details

- `api/metrics.py`: Metrics endpoints
  - `POST /api/metrics` - Submit from agent
  - `GET /api/metrics/{node_id}` - Query historical

#### 3. Agent FastAPI ✓
**Location:** `nexus/agent/`

- `main.py`: Main FastAPI application
  - Lifespan management
  - Registration state tracking (node_id, api_token)
  - Health endpoint with node_id

- `api/system.py`: System information
  - `GET /api/system/info` - System details

- `api/jobs.py`: Job execution
  - `POST /api/jobs/{id}/execute` - Execute job
  - `GET /api/jobs/{id}/status` - Check status

- `services/metrics.py`: Metrics collection
  - Background asyncio service
  - Periodic metric collection
  - Submission to Core

#### 4. CLI Foundation ✓
**Location:** `nexus/cli/`

- `main.py`: Typer app entry point
  - Global config management
  - Rich console output
  - Command group routing
  - Version and info commands

- `commands/config.py`: Configuration management
  - `init` - Interactive configuration wizard
  - `show` - Display current configuration
  - `set` - Update individual settings
  - `validate` - Test connectivity to Core

- `commands/node.py`: Node management
  - `list` - List all nodes with filtering
  - `get` - Get detailed node information
  - `update` - Update node metadata
  - `delete` - Deregister nodes
  - `shell` - Stub for future remote shell (Phase 4)

- `commands/job.py`: Job management
  - `submit` - Submit OCR, shell, or sync jobs
## 🗺️ Future Phases (Roadmap)

> **See the master roadmap:** [ROADMAP.md](ROADMAP.md)


### ✅ Phase 14: Fleet Maintenance (Complete)
**Goal:** Make the fleet maintainable without logging into every node.
- [x] **Agent Updates:** A logical way to update `nexus-agent` code on remote nodes (git pull + restart service).
- [x] **Self-Diagnostics:** improved error reporting when things break.

### 🔒 Phase 15: Security Hardening
**Goal:** Lock the doors before we expand further.
- [ ] **Strict TLS:** Enforce HTTPS everywhere if exposed beyond localhost.
- [ ] **Role Based Access (Maybe):** Simple Admin vs View-Only user.

### 🛑 Phase 15: Stability Freeze
**Goal:** No new features. Only bug fixes and performance tuning.
- [ ] Comprehensive test suite.
- [ ] Long-term memory leak testing.

---

## 🔑 Key Architectural Decisions

1. **FastAPI Everywhere:** Both Core and Agent use FastAPI (not Flask)
   - Better async support
   - Native WebSocket support
   - Built-in OpenAPI docs

2. **Docker-First Service Management:** Docker is the foundational orchestration technology
   - Services deployed as containers across the fleet
   - Consistent deployments regardless of underlying hardware
   - Service templates for common applications (Pi-hole, Home Assistant, etc.)
   - Docker SDK for Python for container management

3. **Debian-Based Platform:** Supports any Debian-derivative Linux distribution
   - Raspberry Pi OS (primary target)
   - Ubuntu Server (x86_64 and ARM)
   - Debian (stable and testing)
   - Platform-specific optimizations (vcgencmd for Pi, lm-sensors for others)

4. **Local Network First:** Designed for LAN, VPN optional
   - Works without ZeroTier/Tailscale
   - VPN is an enhancement, not a requirement
   - Tested with ZeroTier for remote Pi management

5. **SQLite for Core:** Simple, file-based database
   - Sufficient for small-to-medium fleets
   - Easy backup and migration

6. **CLI-First Development:** Every feature gets a CLI command first
   - Web dashboard is optional
   - Automation-friendly from day one

7. **Pydantic for Everything:** All models use Pydantic v2
   - Validation at API boundaries
   - Type-safe throughout

8. **JWT Authentication:** Token-based auth for agents
   - Shared secret for initial registration
   - JWT tokens for ongoing requests

---

## 📂 Important Files to Know

### Configuration
- `.env.example` - Environment variable template
- `pyproject.toml` - Python packaging, dependencies, tools
- `requirements.txt` - Core dependencies
- `requirements-agent.txt` - Agent-specific (psutil, Tesseract)
- `requirements-dev.txt` - Development tools (pytest, black, ruff)

### Documentation
- `README.md` - Project overview and getting started
- `PROGRESS.md` - Detailed progress tracking (keep updated!)
- `docs/architecture.md` - System architecture deep dive
- `docs/api.md` - Complete API specification
- `CONTEXT.md` - This file (context for resuming)

### Code Structure
```
nexus/
├── shared/      # Shared models, config, auth (complete)
├── core/        # Core server (skeleton complete, needs DB)
├── agent/       # Agent server (skeleton complete, needs impl)
├── cli/         # CLI (not started)
└── [modules]/   # Future: Speculum, Imperium, Scriptor, Arbiter
```

---

## 🚀 How to Resume Development

### 1. Environment Setup (First Time)
```bash
# Run the dev setup script
./scripts/dev-setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
```

### 2. Check Current Status
```bash
# View progress
cat PROGRESS.md

# View recent commits
git log --oneline -10

# Check branch
git status
```

### 3. Start Next Task
According to PROGRESS.md, next is: **CLI Foundation**

Start with:
1. Create `nexus/cli/main.py` with Typer app
2. Create `nexus/cli/commands/` modules
3. Implement basic commands (config, node list)

### 4. Testing (When Ready)
```bash
# Core server (when dependencies installed)
python -m nexus.core.main
# Visit http://localhost:8000/docs for OpenAPI

# Agent server
python -m nexus.agent.main
# Visit http://localhost:8001/docs

# CLI
nexus --help
```

---

## ⚠️ Important Notes

### Dependencies Not Yet Installed
The project structure is complete, but dependencies haven't been installed yet. Before running:
```bash
pip install -r requirements-dev.txt
pip install -e .
```

### Database Not Implemented
All Core API endpoints return stubs or 501 errors. Need to:
1. Create SQLAlchemy models in `nexus/core/db/models.py`
2. Set up Alembic migrations
3. Implement actual database queries in API routers

### Agent Needs psutil
Agent metrics collection uses platform module currently. Need to:
1. Install psutil: `pip install psutil`
2. Implement actual metric collection in `services/metrics.py`
3. For Pi temperature: Use `vcgencmd` (gracefully handle non-Pi systems)

### TODO Markers
Search for `TODO:` in the codebase to find all pending implementations:
```bash
rg "TODO:" nexus/
```

---

## 🐛 Known Issues / Gotchas

1. **No .env file yet:** Copy `.env.example` to `.env` and update values
2. **Shared secret default:** Change `NEXUS_SHARED_SECRET` in production
3. **JWT secret default:** Change `NEXUS_JWT_SECRET_KEY` in production
4. **Pi3 Memory:** Only 1GB RAM - keep resource usage low
5. **ARM Architecture:** Test Docker builds on Pi for ARM compatibility

---

## 💡 Development Tips

### Code Style
- Black (line length 100)
- Ruff for linting
- Type hints everywhere (mypy strict mode)
- Docstrings for all public functions

### Git Workflow
- main: Stable releases only
- dev: Active development (current branch)
- Commit frequently with descriptive messages
- Update PROGRESS.md with each major milestone

### Testing Strategy (Future)
1. Unit tests for models and utilities
2. Integration tests for API endpoints
3. End-to-end tests for full workflows
4. Test on laptop first, then deploy to Pi3 for real-world testing

### Performance Considerations for Pi3
- Limit concurrent jobs to 1-2
- Use async patterns throughout
- Keep Docker images lean
- Monitor memory usage carefully
- OCR (Tesseract) will be slow - queue jobs properly

---

## 📝 Session Notes

> **Note:** Older session notes have been archived to keep this file concise.
> See: [docs/archive/session_notes.md](docs/archive/session_notes.md)

