# Nexus Development Context

**Last Session:** 2025-11-30
**Current Branch:** dev
**Current Phase:** Phase 1 - The Bedrock (In Progress)

---

## 🎯 Project Overview

Nexus is a distributed Raspberry Pi management system with a **CLI-first** philosophy. It allows you to manage a fleet of Raspberry Pis from the command line, with an optional web dashboard.

**Target Hardware:**
- Development: Linux laptop (x86_64)
- Testing: Raspberry Pi 3 Model B (ARMv7/v8, 1GB RAM)

---

## ✅ What's Been Completed

### Phase 0: Project Initialization (Complete ✓)
- Full project structure created
- README.md updated with architectural decisions
- Docker configuration (docker-compose.yml, Dockerfiles)
- Comprehensive documentation (docs/architecture.md, docs/api.md)
- Development tooling (scripts/dev-setup.sh, .env.example)
- Git repository initialized with main and dev branches

### Phase 1: The Bedrock (In Progress)

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

---

## 🚧 What's Next

### Immediate: CLI Foundation
**Location:** `nexus/cli/` (not started)

Need to implement:
1. `main.py` - Typer app entry point
2. `commands/config.py` - Config init/management
3. `commands/node.py` - Node list/status/shell
4. `commands/job.py` - Job submit/list/status

### After CLI: Database Layer
**Location:** `nexus/core/db/` (not started)

Need to implement:
1. SQLAlchemy models
2. Alembic migrations
3. Database initialization
4. CRUD operations

Replace all the TODO markers in Core API with actual database queries.

### Then: Connect Core and Agent
1. Implement agent registration flow
2. Implement metrics collection with psutil
3. Implement metrics submission to Core
4. Test end-to-end on laptop

---

## 🔑 Key Architectural Decisions

1. **FastAPI Everywhere:** Both Core and Agent use FastAPI (not Flask)
   - Better async support
   - Native WebSocket support
   - Built-in OpenAPI docs

2. **Local Network First:** Designed for LAN, VPN optional
   - Works without ZeroTier/Tailscale
   - VPN is an enhancement, not a requirement

3. **SQLite for Core:** Simple, file-based database
   - Sufficient for small-to-medium fleets
   - Easy backup and migration

4. **CLI-First Development:** Every feature gets a CLI command first
   - Web dashboard is optional
   - Automation-friendly from day one

5. **Pydantic for Everything:** All models use Pydantic v2
   - Validation at API boundaries
   - Type-safe throughout

6. **JWT Authentication:** Token-based auth for agents
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

**Session 2025-11-30:**
- Completed Phase 0 initialization
- Built shared models, config, and auth
- Implemented Core FastAPI skeleton (all endpoints stubbed)
- Implemented Agent FastAPI skeleton (all endpoints stubbed)
- Next session: Start CLI foundation

**Key Decisions Made:**
- FastAPI everywhere (consistency)
- Local network first (lower barrier)
- Pydantic v2 with strict validation
- JWT with bcrypt for auth
- SQLite for simplicity

---

## 🎯 End Goal for Phase 1

A working system where:
1. ✅ Shared models are complete
2. ✅ Core API structure is complete
3. ✅ Agent API structure is complete
4. ⏳ CLI can interact with Core
5. ⏳ Core has database backing
6. ⏳ Agent can register with Core
7. ⏳ Agent can send metrics to Core
8. ⏳ Can list nodes and see their status via CLI

Once Phase 1 is complete, we'll have a minimal viable system that can be tested end-to-end.

---

**Good luck on the next session! Start with PROGRESS.md and this file to get oriented.**
