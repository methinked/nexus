# Nexus Development Progress

**Last Updated:** 2026-03-14
**Current Phase:** Production Maintenance & Monitoring

---

## � Project Status

### ✅ Completed

#### Phase 0: Project Initialization ✨
- Repository created and cloned
- README.md updated with architecture decisions
- Project structure created (nexus/core, nexus/agent, nexus/cli, tests/)
- Python packaging configuration (pyproject.toml with modern PEP 621 format)
- Dependency management (requirements.txt, requirements-agent.txt, requirements-dev.txt)
- .gitignore configured (Python, IDEs, Nexus-specific patterns)
- Progress tracking system established (PROGRESS.md)
- Documentation structure created
- Docker configuration (docker-compose.yml, Dockerfiles for Core and Agent)
- Development tooling (scripts/dev-setup.sh, .env.example)
- Git repository initialized with dev branch

**Phase 0 Complete: 2025-11-30** 🎉

#### Phase 1: The Bedrock - COMPLETE ✓ (2025-11-30)
- Shared models implementation (`nexus/shared/`)
- Core FastAPI skeleton (`nexus/core/`)
- Agent FastAPI skeleton (`nexus/agent/`)
- CLI foundation (`nexus/cli/`)

**Phase 1 Complete: 2025-11-30** 🎉

#### Phase 1.5: Database Layer - COMPLETE ✓ (2025-11-30)
- Database layer (`nexus/core/db/`)
- Alembic migration system
- Core API updated to use database

**Phase 1.5 Complete: 2025-11-30** 🎉

#### Phase 2: The Mesh - Agent Connectivity (Completed 2025-11-30) ✨
- Development environment setup
- Core server operational
- Agent registration flow
- Real metrics collection with psutil
- End-to-end testing

**Phase 2 Complete: 2025-11-30** 🎉

#### Phase 3: The Pulse - Metrics Visualization (Completed 2025-11-30) ✨
- Enhanced shared models
- Core API metrics enhancements
- Core API health endpoints
- Health calculation service
- CLI metrics commands

**Phase 3 Complete: 2025-11-30** 🎉

#### Phase 4: The Brain - Logging & Remote Control (Completed 2025-11-30) ✨
- Terminal WebSocket architecture designed
- Agent terminal endpoint (Imperium module)
- Core terminal proxy
- Centralized logging system
- Database migration for logs table
- Log CRUD operations
- Log API endpoints
- Agent log collection service
- CLI logs viewer command
- End-to-end testing

**Phase 4 Complete: 2025-11-30** 🎉

#### Phase 5: The Hands - Workload Orchestration (Completed 2025-11-30) ✨
- Job execution architecture designed
- Agent job queue implementation
- Shell executor module
- Job dispatcher service
- Agent job API endpoints
- Core job API enhancements
- Agent lifecycle integration
- Shared model updates
- End-to-end testing

**Phase 5 Complete: 2025-11-30** 🎉

#### Phase 6: The Dashboard - Visualization & Monitoring (Completed 2025-11-30) ✨
- Web dashboard foundation created and tested
- Base template with navigation and responsive layout
- Unique CLI view feature (shows equivalent CLI commands for all API calls)
- CLI view state persistent across page navigation
- Purple dark theme implemented (#7C3AED)
- Dashboard overview page with stat cards and fleet topology
- Real-time metrics charts with Chart.js (CPU, Memory, Disk, Temperature)
- Node detail view with comprehensive information
- WebSocket real-time updates
- Jobs management UI
- Logs viewer UI

**Phase 6 Complete: 2025-11-30** 🎉

#### Phase 7: Docker Orchestration (Removed - Project Pivot)
- Originally planned for service management, but removed to maintain lightweight focus
- Core API and database models were implemented but removed from active development

#### Phase 8-12: UI/UX Refinements (Completed 2025-12-06) ✨
- Chart.js refactoring and performance optimizations
- Service visibility enhancements
- System reliability improvements
- Developer features and stats views

#### Phase 13: Agent Auto-Update & Resilience (Completed 2025-12-20) 🔄
- Agent self-update mechanism
- Core update orchestration
- Dashboard UI integration
- Resilience & bug fixes

#### Phase 14: Fleet Maintenance (Completed 2025-12-21) 🛠️
- Agent update mechanisms
- Self-diagnostics and error reporting

#### Phase 15: ZeroTier Expansion (Completed 2025-12-21) 🌐
- Hybrid network topology
- Agent deployment
- Full fleet status

#### Phase 16: Stability - Automated Testing (In Progress) 🧪
- Test infrastructure setup
- Unit testing initialization
- API integration testing

---

## 🚧 In Progress

_No active development phase at the moment. Phase 4 complete!_

---

## 🎯 Future Features (Planned)

#### Phase 15: Security Hardening
- Strict TLS enforcement
- Role-based access control (Admin vs View-Only)

#### Phase 16: Stability Freeze
- Comprehensive test suite
- Long-term memory leak testing
- Performance tuning

#### Medium Priority (Post-Dashboard)
- Job Scheduling - Cron-like scheduling for recurring jobs
- Terminal CLI Client - WebSocket-based remote shell client
- Job Templates - Pre-defined job configurations for common tasks

#### Optional (Vigil Legacy - Parked)
- Scriptor Module (OCR) - Tesseract integration (infrastructure ready)
- Arbiter Module (Sync) - Syncthing conflict resolution (infrastructure ready)

---

## 🏗️ Project Structure

```
nexus/
├── .gitignore
├── README.md
├── LICENSE
├── PROGRESS.md
├── pyproject.toml
├── requirements.txt
├── requirements-agent.txt
├── requirements-dev.txt
├── docker-compose.yml          # TODO
├── docs/
│   ├── architecture.md         # TODO
│   └── api.md                  # TODO
├── nexus/
│   ├── __init__.py
│   ├── core/                   # Core server
│   │   ├── __init__.py
│   │   ├── main.py             # TODO - FastAPI app entry
│   │   ├── api/                # FastAPI routes
│   │   ├── db/                 # Database models/migrations
│   │   └── services/           # Business logic
│   ├── agent/                  # Agent server
│   │   ├── __init__.py
│   │   ├── main.py             # TODO - FastAPI app entry
│   │   ├── api/                # FastAPI routes
│   │   ├── modules/            # Scriptor, Speculum, etc.
│   │   └── services/
│   ├── cli/                    # CLI
│   │   ├── __init__.py
│   │   ├── main.py             # TODO - Typer app entry
│   │   └── commands/
│   ├── shared/                 # Shared utilities
│   │   ├── __init__.py
│   │   ├── auth.py             # TODO
│   │   └── models.py           # TODO
├── tests/
│   ├── __init__.py
│   ├── core/
│   ├── agent/
│   └── cli/
└── scripts/
    └── dev-setup.sh            # TODO
```

---

## 🔑 Key Architectural Decisions

1. **FastAPI Everywhere:** Using FastAPI for both Core and Agent for consistency, modern async support, and native WebSocket capabilities.

2. **Local Network First:** Design assumes local network connectivity by default. VPN (ZeroTier/Tailscale) is an optional layer for remote access.

3. **SQLite for Core:** Simple, file-based database sufficient for managing a fleet of Raspberry Pis.

4. **CLI-First Development:** Every feature gets a CLI command before a web UI.

5. **Modular Agent Components:** Each agent module (Speculum, Imperium, Scriptor, Arbiter) is independently deployable.

---

## 🐛 Known Issues

None yet - project just initialized!

---

## 💡 Ideas / Future Considerations

- Consider adding mDNS/Avahi for local network discovery
- Investigate SQLite performance limits for fleet size
- Plan for graceful degradation when Core is unreachable
- Consider adding a "local mode" where Agent can function independently
- Explore using NATS or Redis for pub/sub if fleet grows large
- Add metrics dashboard using something lightweight (htmx + charts?)

---

## 📝 Notes

- Keep this file updated at each significant milestone
- Document blockers and decisions here for future reference
- Update "Last Updated" date when making changes

### Development Environment
- **Primary Dev:** Linux laptop (x86_64)
- **Test Deployment:** Raspberry Pi 3 Model B (ARMv7/v8, 1GB RAM)
- **Considerations:** Keep resource usage low for Pi3 constraints

### Performance Guidelines for Pi3
- Limit concurrent jobs to 1-2 per node
- Optimize Docker images for ARM architecture
- Use async patterns to maximize limited CPU
- Monitor memory usage carefully (only 1GB available)

---

## 📅 Roadmap Highlights

See [ROADMAP.md](ROADMAP.md) for full details.

### Immediate Focus
1.  **Phase 15: Security** (RBAC, TLS, Secure Token Handling)
2.  **Phase 4 (Refined):** Advanced Logs & Alerts
3.  **Phase 6 (Refined):** Dashboard "Day 2" Features
- ✅ Health status display (Overall, CPU, Memory, Disk)
- ✅ Real-time metrics charts (4 charts per node):
  - CPU Usage with current value display (e.g., 15.3%)
  - Memory Usage with current value
  - Disk Usage with current value
  - Temperature with current value
  - Proper labels, titles, and axis units
  - Time axis formatted as HH:mm
  - Dark-themed tooltips
  - Auto-refresh every 30 seconds
- ✅ Agent services status display (Metrics, Logging, Job Dispatcher)
- ✅ Recent jobs list (last 5 jobs)
- ✅ Recent logs preview (last 20 entries)
- ✅ CLI view integration (all API calls logged)
- ✅ Loading states and error handling
- ✅ Tested with both laptop + Pi nodes

**Modules Preview (2025-11-30 Late Night):**
- ✅ **Modules & Services stub page created** (Phase 7 preview)
- ✅ Available modules grid showing:
  - Docker Engine, Pi-hole, Home Assistant, Prometheus, Grafana
  - Module cards with icons, versions, descriptions
  - Deployment status (0/2 nodes)
  - Deploy buttons (stub)
- ✅ Deployment status table for all nodes
- ✅ Coming soon notice with Phase 7 vision
- ✅ Added "Modules" to navigation (desktop + mobile)
- ✅ Route: /modules

**Phase 6.2 Node Detail View COMPLETE!** ✓ - Production-ready node management and monitoring

**WebSocket Real-time Updates (2025-11-30 Late Night):**
- ✅ **WebSocket system implemented - COMPLETE!**
- ✅ WebSocket connection manager:
  - Manages multiple client connections
  - Broadcasts events to all connected clients
  - Thread-safe with asyncio locks
  - Personal message support
  - Connection tracking and cleanup
- ✅ WebSocket endpoint (/api/ws):
  - Accepts WebSocket connections
  - Handles ping/pong for keepalive
  - Connection success messages
  - Proper error handling and disconnection
- ✅ Broadcast system:
  - Metric updates broadcast when agents submit
  - Event types: metric_update, node_status, job_update, log_entry
  - JSON message format with type and data
- ✅ Client-side WebSocket library:
  - Auto-connect on page load
  - Reconnection with exponential backoff (max 5 attempts)
  - Event listener system (on/off/emit)
  - Ping/pong keepalive (30s interval)
  - Graceful fallback to polling after max reconnect attempts
- ✅ Dashboard real-time updates:
  - Removed 30-second polling
  - Instant updates on metric changes
  - Fallback to polling if WebSocket fails
  - Re-enables WebSocket on reconnection
- ✅ Nodes page real-time updates:
  - Instant metric updates for selected node
  - Node list updates (last seen times)
  - Smart fallback handling
  - Seamless reconnection
- ✅ Benefits:
  - **Instant updates** instead of 30-second delay
  - Lower bandwidth usage (push vs pull)
  - More responsive user experience
  - Professional real-time dashboard
  - Reliable with automatic fallback

**Phase 6.2 + WebSocket COMPLETE!** ✓ - Real-time monitoring with instant updates

**Jobs Management UI (2025-12-01 Morning):**
- ✅ **Phase 6.3 Job Management UI - COMPLETE!**
- ✅ Comprehensive jobs page at /jobs
- ✅ Job listing table with columns:
  - Status badges (pending, running, completed, failed)
  - Job type (SHELL, OCR, SYNC)
  - Node name display
  - Command preview
  - Created timestamp (relative time)
  - Duration calculation
  - Details button
- ✅ Stats cards (Total, Running, Completed, Failed)
- ✅ Filter tabs (All, Running, Completed, Failed)
- ✅ Job details modal:
  - Full job information display
  - Command/payload view
  - Output viewer with syntax highlighting
  - Error display with red theme
  - Timestamps for created/started/completed
- ✅ Job submission form modal:
  - Job type selector (Shell, OCR-disabled, Sync-disabled)
  - Node dropdown with IP addresses
  - Command textarea (multi-line)
  - Timeout configuration (1-3600s)
  - Form validation
  - Submit to /api/jobs endpoint
- ✅ Real-time updates via WebSocket
- ✅ Fallback polling (30s interval)
- ✅ Responsive design with purple theme
- ✅ CLI view integration
- ✅ Empty state handling
- ✅ Error handling and user feedback

**Phase 6.3 COMPLETE!** ✓ - Full-featured job management via web UI

---

#### Phase 7.1: Core Service Management API - Docker Orchestration (2025-12-01 Evening)

**Status:** ❌ REMOVED (2025-12-28 - Project pivot to lightweight monitoring)

**Goal:** Build the foundational database layer and API for Docker service orchestration.

**Completed Tasks:**
- ✅ **Database Models:**
  - ServiceModel: Docker service templates with compose YAML
  - DeploymentModel: Service deployment instances per node
  - DeploymentStatus enum (DEPLOYING, RUNNING, STOPPED, FAILED, REMOVING)

- ✅ **Pydantic Models** (12 new models):
  - Service, ServiceCreate, ServiceUpdate, ServiceList
  - Deployment, DeploymentCreate, DeploymentUpdate, DeploymentList
  - DeploymentConfig, DeploymentWithDetails, ContainerStatus

- ✅ **Database Migration:**
  - services table with indexes and unique constraints
  - deployments table with foreign keys (CASCADE delete)
  - Alembic migration successfully applied

- ✅ **CRUD Operations** (28 functions):
  - Services: create, get, get_by_name, list, count, update, delete
  - Deployments: create, get, list, count, update, update_status, delete
  - Full filtering support (category, node, service, status)
  - Pagination support

- ✅ **API Endpoints** (13 RESTful endpoints):
  - **Services API** (/api/services):
    - GET /api/services - List service templates
    - GET /api/services/{id} - Get service details
    - POST /api/services - Create custom service template
    - PUT /api/services/{id} - Update service template
    - DELETE /api/services/{id} - Delete service template

  - **Deployments API** (/api/deployments):
    - GET /api/deployments - List deployments
    - GET /api/deployments/{id} - Get deployment details
    - POST /api/deployments - Deploy service to node
    - PUT /api/deployments/{id} - Update deployment config
    - POST /api/deployments/{id}/start - Start stopped deployment
    - POST /api/deployments/{id}/stop - Stop running deployment
    - POST /api/deployments/{id}/restart - Restart deployment
    - DELETE /api/deployments/{id} - Remove deployment

- ✅ **Validation:**
  - Service name uniqueness enforced
  - Node must be ONLINE to accept deployments
  - Service and node existence validated before deployment

- ✅ **Integration:**
  - Routers registered in main FastAPI app
  - All imports and exports wired correctly
  - Server starts successfully with new endpoints
  - OpenAPI documentation auto-generated

**Technical Debt:**
- TODO markers added for Phase 7.4 (deployment workflow)
- Agent-side Docker operations not yet implemented

**Files Changed:**
- 10 files modified/created
- 1000+ lines of code added
- 3 new files: services.py, deployments.py, migration

**What's Next (Phase 7.2):**
- Agent Docker module (docker SDK for Python)
- Container lifecycle management on agents
- Real Docker operations

**Deployment and Testing:**
- ✅ **Git Workflow:**
  - All work committed to dev branch
  - Merged dev → main (26 files, 3958 lines added)
  - Pushed to origin/main
  - Switched back to dev for continued work

- ✅ **Pi Agent Deployment:**
  - Deployed latest code to moria-pi (10.243.14.179) via ZeroTier
  - Fixed port conflict: Old agent process blocking port 8001
  - Killed old process (PID 128696), restarted agent
  - Verified production mode: No watchfiles/reload
  - Confirmed metrics flowing every 30s

- ✅ **Fleet Verification:**
  - 2 nodes online: default-agent (laptop) + moria-pi (Pi)
  - Real-time metrics: CPU 8.1%, Memory 25.9%, Disk 14.4%, Temp 45.1°C
  - Health endpoint responding correctly
  - WebSocket updates working across fleet
  - All 13 new API endpoints operational

**Phase 7.1 COMPLETE!** ✓ - Foundation ready for Docker orchestration
**System Status:** Production-ready on real hardware (laptop + Raspberry Pi)

---

#### Phase 7.2.5: Docker CLI Commands (2025-12-03 Evening)

**Status:** ❌ REMOVED (2025-12-28 - Project pivot to lightweight monitoring)

**Goal:** Provide CLI-first interface for Docker service and deployment management.

**Completed Features:**
- ✅ **Service Management Commands** (nexus/cli/commands/service.py - 302 lines):
  - `nexus service list` - List all service templates with Rich table formatting
  - `nexus service get <id>` - View service details in formatted panel
  - `nexus service create` - Create service templates with ports, volumes, environment
  - `nexus service delete <id>` - Delete service templates with confirmation
  - Port parsing: Supports host:container and host:container/protocol formats
  - Volume parsing: Supports host:container mappings
  - Environment parsing: Supports KEY=VALUE format
  - Comprehensive error handling and user feedback

- ✅ **Deployment Management Commands** (nexus/cli/commands/deployment.py - 407 lines):
  - `nexus deployment list` - List deployments with filtering (--node, --status)
  - `nexus deployment get <id>` - View deployment details
  - `nexus deployment create <service_id> <node_id>` - Deploy service to node
  - `nexus deployment start <id>` - Start stopped deployment
  - `nexus deployment stop <id>` - Stop running deployment
  - `nexus deployment restart <id>` - Restart deployment
  - `nexus deployment delete <id>` - Remove deployment with confirmation
  - Environment variable overrides via -e flag
  - Color-coded status badges (green/yellow/red)
  - Rich table and panel formatting

- ✅ **CLI Integration:**
  - Commands registered in nexus/cli/main.py
  - Consistent with existing CLI patterns (node, job, metrics, logs)
  - Uses CLIConfig for Core URL and authentication
  - httpx for HTTP requests to Core API
  - Rich console for beautiful terminal output

- ✅ **User Experience:**
  - Helpful examples in docstrings
  - Confirmation prompts for destructive operations
  - --yes flag to skip confirmations for automation
  - Detailed error messages with HTTP status codes
  - Next-step suggestions after operations

**Examples:**
```bash
# Service management
nexus service list
nexus service create -n nginx -i nginx:latest -p 80:80 -v /data:/usr/share/nginx/html
nexus service get f6b858e2
nexus service delete f6b858e2

# Deployment management
nexus deployment list --status running
nexus deployment create f6b858e2 a1b2c3d4 -e PORT=8080
nexus deployment start f6b858e2
nexus deployment stop f6b858e2
nexus deployment restart f6b858e2
nexus deployment delete f6b858e2 --yes
```

**Files:**
- nexus/cli/commands/service.py (302 lines)
- nexus/cli/commands/deployment.py (407 lines)
- nexus/cli/main.py (updated with command registration)

**Phase 7.2.5 COMPLETE!** ✓ - CLI-first Docker orchestration operational
**Note:** These commands were implemented alongside Phase 7.1-7.2 but not previously documented.

---

#### Phase 7.3: Pre-built Docker Service Templates (2025-12-04 Evening)

**Status:** ❌ REMOVED (2025-12-28 - Project pivot to lightweight monitoring)

**Goal:** Provide ready-to-deploy service templates for popular homelab applications.

**Completed Features:**
- ✅ **Service Template Library** (nexus/core/services/service_templates.py - 220 lines):
  - 7 pre-built templates for popular services:
    - **Pi-hole** - Network-wide ad blocking via DNS sinkhole
    - **Home Assistant** - Open source home automation platform
    - **Prometheus** - Monitoring system and time series database
    - **Grafana** - Analytics and visualization platform
    - **Portainer** - Docker container management UI
    - **Nginx Proxy Manager** - Reverse proxy with SSL certificate management
    - **Nextcloud** - Self-hosted cloud storage and collaboration
  - Each template includes:
    - Display name and description
    - Docker Compose YAML configuration
    - Default environment variables
    - Icon URL for web UI
    - Category classification (networking, automation, monitoring, management, storage)
  - Helper functions: get_all_templates(), get_template_by_name(), get_templates_by_category(), get_categories()

- ✅ **Automatic Template Seeding** (nexus/core/services/seed_templates.py - 81 lines):
  - Idempotent seeding on Core startup
  - Checks for existing templates to avoid duplicates
  - Logs seeding results (created, skipped, errors)
  - Integrated into Core lifespan management
  - Database-backed template storage

- ✅ **Enhanced Web UI** (nexus/web/templates/services.html):
  - **Category Filtering:**
    - Dynamic category tabs based on available templates
    - "All" category shows everything
    - Category counts displayed
  - **Search Functionality:**
    - Real-time search across name, description, and category
    - Case-insensitive filtering
    - Instant results without page reload
  - **Improved Service Cards:**
    - Display name and description
    - Category badges with color coding
    - Version information
    - Deploy and view details buttons
  - **Separate Modals:**
    - Create Template Modal - For custom service templates
    - Deploy Modal - For deploying existing templates to nodes
    - Details Modal - For viewing full template configuration
  - **Better Form Validation:**
    - Required fields enforced
    - Docker Compose YAML textarea with monospace font
    - Category selection dropdown
    - Display name vs internal name distinction

- ✅ **Core Integration:**
  - Template seeding runs automatically on Core startup
  - Logs seeding summary (e.g., "Seeded 7 new templates: pihole, homeassistant, ...")
  - Templates stored in database for persistence
  - No duplicate templates created on restart

**Technical Implementation:**
- Service templates defined as Python dictionaries
- Docker Compose YAML stored as multi-line strings
- Category-based organization for UI filtering
- Icon URLs for visual identification
- Default environment variables for easy customization

**Files Created/Modified:**
- nexus/core/services/service_templates.py (new file, 220 lines)
- nexus/core/services/seed_templates.py (new file, 81 lines)
- nexus/core/main.py (+15 lines): Template seeding integration
- nexus/web/templates/services.html (~200 lines modified): Enhanced UI

**End-to-End Testing (2025-12-06):**
- ✅ **Successful Pi-hole deployment to moria-pi:**
  - Docker installed on moria-pi (v29.1.2)
  - Agent restarted with Docker socket access
  - Deployment created via API: `pihole-moria-v3`
  - Container ID: `5257cebbe569`
  - Status: Running & Healthy
  - Web UI accessible: http://192.168.0.78/admin/
  - DNS server operational on port 53

- ✅ **Critical Bug Fixes During Testing:**
  - Fixed docker-compose YAML parsing in deployments API (nexus/core/api/deployments.py:214-271)
  - Added volume path conversion: relative paths (`./data`) → absolute paths (`/opt/nexus/deployments/{id}/data`)
  - Fixed deployment config handling (DeploymentConfig object vs dict)
  - Created deployment directory structure on agent: `/opt/nexus/deployments/`

- ✅ **Verified End-to-End Pipeline:**
  - Service template → API → YAML parsing → Agent → Docker container
  - Image pull: `pihole/pihole:latest` (pulled successfully)
  - Port mappings: 53/tcp, 53/udp, 80/tcp (bound correctly)

**Phase 7.3 COMPLETE!** ✓ - Pre-built service templates operational

---

#### Phase 13: Agent Auto-Update & Resilience (Completed 2025-12-20) 🔄

**Status:** ✅ COMPLETE

**Goal:** Enable remote self-updating of agents from the Core Dashboard to ensure the fleet stays in sync.

**Completed Features:**
- ✅ **Agent Self-Update Mechanism:**
  - `update_agent.sh` script detects git branch and pulls latest code
  - Handles dependency updates (`pip install`) automatically
  - Gracefully restarts the agent service
  - Robust error handling and fallback to 'dev' branch
- ✅ **Core Update Orchestration:**
  - New `UPDATE` job type in Core API
  - `POST /api/update/nodes/{node_id}/update` endpoint
  - `UpdateExecutor` in Job Dispatcher to trigger updates
- ✅ **Dashboard UI Integration:**
  - "Update Agent" button on Node Detail page
  - Visual feedback during update (Offline -> Online transition)
- ✅ **Resilience & Bug Fixes:**
  - **Re-registration Support:** Core now allows existing nodes to re-register (critical for post-update recovery)
  - **Crash Loop Fix:** Resolved async/await syntax error in metrics collector
  - **Deployment Fix:** Fixed variable expansion in `update-agents.sh` script
  - **Stale Alerts:** Fixed `AlertService` to properly sync offline status

**Verification:**
- Validated on `moria-pi`, `orthanc-pi`, and `bywater-pi`
- Full fleet update performed successfully
- All nodes returned to Online status automaticallly

**Phase 13 COMPLETE!** ✓ - Fleet is now self-updating and resilient

---

#### Phase 14: Quality of Life & Polish (Planned) 💅

**Goal:** Refine the user experience based on real-world usage feedback.

**Planned Features:**
- [ ] **Enhanced Container Detection:**
  - Improve `DockerService` to detect rootless Docker and non-standard sockets.
  - Parse `org.opencontainers.image.*` labels for friendly descriptions and icons.
  - Centralize Docker logic (remove duplication in `inventory.py`).
  - Better handling of image tags/digests (resolve `sha256:` to readable names).
- [ ] **UI/UX Improvements:**
  - "Copy to Clipboard" buttons for API tokens and logs.
  - Better mobile responsiveness for tables.
  - collapsible/expandable sections in Node Detail view.

  - Volume mounts: etc-pihole, etc-dnsmasq.d (created on agent)
  - Container startup and health check (passed)

**Phase 7.3 COMPLETE!** ✓ - Docker orchestration tested and operational

**What's Next (Phase 7.3 Expansion - Optional):**
- [ ] Add more service templates (Jellyfin, Plex, Transmission, Sonarr, Radarr, etc.)
- [ ] Template versioning and update mechanism
- [ ] Template marketplace/sharing (future consideration)

---

#### Phase 7.4: Production Hardening - Docker & Storage (IDENTIFIED 2025-12-06)

**Status:** 📋 PLANNED

**Goal:** Make Nexus production-ready for Raspberry Pi deployments with proper storage management.

**Critical Issues Identified:**
1. **Automatic Docker Installation:**
   - Problem: Agents currently fail silently if Docker is not installed
   - Impact: Manual SSH required to install Docker on each agent
   - Solution Needed:
     - Agent startup should detect Docker availability
     - If missing, either auto-install (requires sudo) or fail with clear instructions
     - Log clear error messages to Core for visibility in UI
     - Add Docker installation status to agent health checks

2. **External Storage for Docker (CRITICAL for Pi longevity):**
   - Problem: Docker writes to SD card by default, causing premature wear/failure
   - Impact: SD cards fail after weeks/months of Docker use
   - Solution Needed:
     - Detect external storage (USB drives, SSDs) on agent startup
     - Configure Docker daemon to use external storage: `/etc/docker/daemon.json` with `data-root`
     - Default paths: `/mnt/docker` or `/opt/docker` (external storage)
     - Fallback to SD card only if no external storage detected
     - Add storage location to agent metadata and display in UI
     - Warn user in UI if agent is using SD card for Docker

**Planned Tasks:**
- [ ] Agent: Docker availability check on startup
- [ ] Agent: External storage detection (check `/mnt`, `/media`, `/opt`)
- [ ] Agent: Docker daemon configuration for external storage
- [ ] Agent: Auto-install Docker script (optional, requires sudo)
- [ ] Core: Display Docker storage location in Nodes UI
- [ ] Core: Health warning for SD card Docker usage
- [ ] Documentation: Setup guide for external storage on Pi

**Benefits:**
- Zero-touch Docker setup on new agents
- SD card longevity (years instead of months)
- Production-ready Raspberry Pi deployments
- Better operator visibility into storage health

**Phase 7.4 Status:** 📋 Identified and planned, awaiting implementation

---

#### Phase 6.4: Log Viewer UI (2025-12-01 Evening)

**Status:** ✅ COMPLETE

**Goal:** Build comprehensive web-based log viewer with filtering and search capabilities.

**Completed Features:**
- ✅ **Full-featured log table:**
  - Time, level, node, source, and message columns
  - Color-coded level badges (debug, info, warning, error, critical)
  - Sortable and paginated (50 logs per page)
  - Click row to view full details

- ✅ **Comprehensive filtering:**
  - Node filter dropdown
  - Level filter (debug, info, warning, error, critical)
  - Source filter with text search
  - Message search across all logs
  - Time range selection (1h, 6h, 24h, 7d, all time)

- ✅ **Log detail modal:**
  - Full timestamp and metadata display
  - Complete message with formatting
  - Extra data in JSON format
  - Easy-to-read layout

- ✅ **Real-time updates:**
  - Auto-refresh every 30 seconds
  - Manual refresh button
  - Non-blocking async loading

- ✅ **User experience:**
  - Loading states and spinners
  - Empty state handling
  - Responsive design
  - Keyboard navigation support
  - CLI view integration (all API calls logged)

**Technical Implementation:**
- Alpine.js for state management
- Fetch API for log retrieval
- Client-side filtering for instant results
- Pagination with page tracking
- Time-based queries to Core API

**Phase 6.4 COMPLETE!** ✓ - Full log management interface operational

---

#### Phase 6.5.1: Multi-Disk Detection (Agent) (2025-12-01 Evening)

**Status:** ✅ COMPLETE

**Goal:** Implement comprehensive disk detection and analysis on agents to support smart storage placement for Docker and logs.

**Completed Features:**
- ✅ **Pydantic Models** (nexus/shared/models.py):
  - DiskType enum: SD_CARD, EXTERNAL_SSD, EXTERNAL_HDD, NVME, USB_FLASH, UNKNOWN
  - DiskInfo model: Complete disk information with 16 fields
  - Exported from nexus.shared for agent usage

- ✅ **Disk Detection Module** (nexus/agent/services/storage.py - 304 lines):
  - `detect_disk_type()`: Smart disk type detection using /sys/block/* kernel interface
  - `get_all_disks()`: Comprehensive disk enumeration with psutil
  - `check_docker_data_path()`: Detect if Docker data is on this disk
  - `check_nexus_data_path()`: Detect if Nexus data/logs are on this disk
  - `get_filesystem_label()`: Read disk labels from /dev/disk/by-label
  - `get_filesystem_uuid()`: Read UUIDs from /dev/disk/by-uuid
  - `find_best_storage_disk()`: Smart recommendation (prefer SSD > HDD > root)
  - `format_disk_size()`: Human-readable size formatting

- ✅ **Disk Type Detection Logic:**
  - SD cards: mmcblk* devices → DiskType.SD_CARD
  - NVMe SSDs: nvme* devices → DiskType.NVME
  - SATA/USB devices (sd*):
    - Read /sys/block/{device}/queue/rotational flag
    - rotational=0 → EXTERNAL_SSD
    - rotational=1 → EXTERNAL_HDD
  - Fallback: DiskType.UNKNOWN

- ✅ **MetricsCollector Integration** (nexus/agent/services/metrics.py):
  - Import get_all_disks() from storage module
  - Collect all disk info during metrics collection
  - Log detected disks for debugging (mount, type, usage, flags)
  - Maintain backward compatibility: disk_percent uses root filesystem
  - Graceful fallback if disk detection fails

- ✅ **Testing on Development Machine:**
  - Detected 5 disks correctly (btrfs subvolumes, NVMe boot)
  - Correctly identified Nexus data location
  - Type detection working for all disk types

- ✅ **Testing on Raspberry Pi (moria-pi):**
  - **Detected 3 disks:**
    1. Root SD card (/dev/mmcblk0p2): 28.7 GB, 14.4% used, Nexus data ✓
    2. Boot SD card (/dev/mmcblk0p1): 510 MB boot partition ✓
    3. External HDD (/dev/sda1 at /mnt/data): 465.8 GB, nearly empty ✓
  - **Type detection verified:**
    - mmcblk devices correctly identified as SD_CARD
    - sda device with rotational=1 correctly identified as EXTERNAL_HDD
  - **Smart storage recommendation:**
    - Correctly recommended /mnt/data (external HDD) for Docker/logs
    - Meets minimum free space requirements (465.2 GB free)
  - **Metrics flowing to Core:**
    - Disk percentage: 14.4% (root filesystem) ✓
    - Backward compatibility maintained ✓
    - Agent running successfully with new code ✓

**Technical Implementation:**
- Uses psutil.disk_partitions() for disk enumeration
- Reads Linux kernel /sys/block/* for device properties
- Filters virtual filesystems (tmpfs, devtmpfs, squashfs, overlay)
- Detects data location by checking file paths
- Sorts disks: root filesystem first, then alphabetically

**Files Created/Modified:**
- nexus/shared/models.py (+67 lines): DiskInfo and DiskType models
- nexus/shared/__init__.py: Export new models
- nexus/agent/services/storage.py (new file, 304 lines): Disk detection module
- nexus/agent/services/metrics.py (+25 lines): Integration with MetricsCollector

**What's Next (Phase 6.5.2):**
- Database schema extension (add disks_json column to metrics table)
- Update MetricCreate to include disk array
- Store multi-disk data in Core database
- API endpoints for disk information queries

**Phase 6.5.1 COMPLETE!** ✓ - Agent disk detection operational on real hardware

---

## 🎯 Future Features (Planned)

#### Phase 6.5: Multi-Disk Storage Support (IN PROGRESS)
- ✅ Phase 6.5.1: Agent disk detection - COMPLETE
- 🚧 Phase 6.5.2: Database schema and metrics storage
- 🚧 Phase 6.5.3: Smart storage placement (auto-configure Docker to external disk)
- 🚧 Phase 6.5.4: Dashboard multi-disk UI
- 🚧 Phase 6.5.5: Alerts and documentation
- **Estimated Effort:** 2 weeks total (6 days remaining)

#### Phase 6.6: Advanced Dashboard Features
- Terminal in browser (xterm.js)
- Alerting system with notifications
- User authentication and access control
- **Estimated Effort:** 2-3 weeks per feature

**Medium Priority (Post-Dashboard):**
- **Job Scheduling** - Cron-like scheduling for recurring jobs
- **Terminal CLI Client** - WebSocket-based remote shell client
- **Job Templates** - Pre-defined job configurations for common tasks

**Optional (Vigil Legacy - Parked):**
- **Scriptor Module (OCR)** - Tesseract integration (infrastructure ready)
- **Arbiter Module (Sync)** - Syncthing conflict resolution (infrastructure ready)

---

## 🏗️ Project Structure

```
nexus/
├── .gitignore
├── README.md
├── LICENSE
├── PROGRESS.md
├── pyproject.toml
├── requirements.txt
├── requirements-agent.txt
├── requirements-dev.txt
├── docker-compose.yml          # TODO
├── docs/
│   ├── architecture.md         # TODO
│   └── api.md                  # TODO
├── nexus/
│   ├── __init__.py
│   ├── core/                   # Core server
│   │   ├── __init__.py
│   │   ├── main.py             # TODO - FastAPI app entry
│   │   ├── api/                # FastAPI routes
│   │   ├── db/                 # Database models/migrations
│   │   └── services/           # Business logic
│   ├── agent/                  # Agent server
│   │   ├── __init__.py
│   │   ├── main.py             # TODO - FastAPI app entry
│   │   ├── api/                # FastAPI routes
│   │   ├── modules/            # Scriptor, Speculum, etc.
│   │   └── services/
│   ├── cli/                    # Typer CLI
│   │   ├── __init__.py
│   │   ├── main.py             # TODO - Typer app entry
│   │   └── commands/
│   ├── shared/                 # Shared utilities
│   │   ├── __init__.py
│   │   ├── auth.py             # TODO
│   │   └── models.py           # TODO
├── tests/
│   ├── __init__.py
│   ├── core/
│   ├── agent/
│   └── cli/
└── scripts/
    └── dev-setup.sh            # TODO
```

---

## 🔑 Key Architectural Decisions

1. **FastAPI Everywhere:** Using FastAPI for both Core and Agent for consistency, modern async support, and native WebSocket capabilities.

2. **Local Network First:** Design assumes local network connectivity by default. VPN (ZeroTier/Tailscale) is an optional layer for remote access.

3. **SQLite for Core:** Simple, file-based database sufficient for managing a fleet of Raspberry Pis.

4. **CLI-First Development:** Every feature gets a CLI command before a web UI.

5. **Modular Agent Components:** Each agent module (Speculum, Imperium, Scriptor, Arbiter) is independently deployable.

---

## 🐛 Known Issues

None yet - project just initialized!

---

## 💡 Ideas / Future Considerations

- Consider adding mDNS/Avahi for local network discovery
- Investigate SQLite performance limits for fleet size
- Plan for graceful degradation when Core is unreachable
- Consider adding a "local mode" where Agent can function independently
- Explore using NATS or Redis for pub/sub if fleet grows large
- Add metrics dashboard using something lightweight (htmx + charts?)

---

## 📝 Notes

- Keep this file updated at each significant milestone
- Document blockers and decisions here for future reference
- Update "Last Updated" date when making changes

### Development Environment
- **Primary Dev:** Linux laptop (x86_64)
- **Test Deployment:** Raspberry Pi 3 Model B (ARMv7/v8, 1GB RAM)
- **Considerations:** Keep resource usage low for Pi3 constraints

### Performance Guidelines for Pi3
- Limit concurrent jobs to 1-2 per node
- Optimize Docker images for ARM architecture
- Use async patterns to maximize limited CPU
- Monitor memory usage carefully (only 1GB available)

---

## 📅 Session: 2025-12-02 Evening - UI Polish, Multi-Disk Display & Error Handling Standards

### Phase 7.2: Agent Docker Module - COMPLETE ✅

**All components implemented and tested:**
- [x] Docker SDK for Python integration (docker>=7.0.0)
- [x] Agent Docker service (`nexus/agent/services/docker.py`)
  - Container lifecycle: create, start, stop, restart, remove
  - Image pulling with progress
  - Container status and health monitoring
  - Resource usage stats (CPU, memory)
  - Container logs retrieval
  - Nexus-managed container labeling
- [x] Agent Docker API endpoints (`nexus/agent/api/docker.py`)
  - POST /api/docker/deploy - Deploy and start containers
  - POST /api/docker/{id}/start|stop|restart - Lifecycle control
  - DELETE /api/docker/{id} - Remove containers
  - GET /api/docker/{id}/status - Detailed status
  - GET /api/docker/{id}/logs - Container logs
  - GET /api/docker/containers/list - List all Nexus containers
- [x] Core deployment orchestration (`nexus/core/api/deployments.py`)
  - Send deployment requests to agents via HTTP
  - Container lifecycle commands proxied to agents
  - Error handling for agent communication failures
- [x] CLI commands for services and deployments
  - `nexus service create|list|get|delete` - Service template management
  - `nexus deployment create|list|get|start|stop|restart|delete` - Deployment lifecycle
- [x] Web dashboard for Docker orchestration
  - Services page: Create/manage service templates
  - Deployments page: Deploy and manage containers across fleet
  - Real-time status updates with color-coded indicators

**Phase 7.2 Complete: 2025-12-02** 🎉

### UI Fixes & Improvements

**Health Status Display Issues Resolved:**
- [x] Fixed "undefined" display in health status cards (commit `6b980c0`)
  - Issue: Template was accessing wrong field paths
  - Fix: Changed to `healthStatus.latest_metrics.cpu_percent` format
- [x] Added temperature card to health status display (commit `0b2f611`)
  - Changed grid from 4 to 5 columns
  - Shows temperature with °C unit and color coding
  - Falls back to 'N/A' if sensor unavailable
- [x] Fixed health status value comparisons (commit `7e562bc`)
  - Issue: API returns lowercase ("healthy") but template checked uppercase ("HEALTHY")
  - Fix: Updated all comparisons to lowercase, display still shows uppercase via `.toUpperCase()`

**Multi-Disk Display Implementation:**
- [x] Agent disk information endpoint (commit `319f5e6`)
  - GET /api/system/disks - Returns all mounted disks with DiskInfo
  - Uses existing `get_all_disks()` from Phase 6.5.1
- [x] Core disk information proxy (commit `319f5e6`)
  - GET /api/nodes/{node_id}/disks - Fetches from agent
  - Validates response and handles communication errors
- [x] Web dashboard storage devices section (commit `319f5e6`)
  - Displays all disks with mount points and device paths
  - Color-coded disk type badges (SD Card, External SSD, External HDD, NVMe, USB Flash)
  - Usage percentages with color-coded progress bars (green/amber/red)
  - Free space in human-readable format
  - Special badges: System, Docker Data, Nexus Data, Read-Only
  - Helper functions: `formatDiskType()` and `formatBytes()`
- [x] Storage error handling (commit `29e6fd5`)
  - Shows clear error message when agent lacks endpoint
  - Displays update instructions with command
  - Prevents "undefined" from appearing

### Error Handling Standards Established

**CRITICAL RULE Documented (commit `bbea328`):**
> All error messages must be clear, actionable, and avoid "undefined" or generic failures.

**New Documentation: `docs/CONTRIBUTING.md`**
- [x] Error message clarity principles (what, why, how)
- [x] Good vs bad error message examples
- [x] Frontend error handling checklist
  - Always provide fallback values: `value || 'N/A'`
  - Check data existence: `value?.property`
  - Show error states explicitly with flags
  - Track loading/error/empty states separately
- [x] Backend error handling checklist
  - Use appropriate HTTP status codes
  - Include context in error messages
  - Provide actionable next steps
  - Log errors with full details
- [x] Testing error scenarios checklist
  - API 404/500 responses, timeouts, malformed data
  - Missing/null fields, empty arrays
  - Agent offline scenarios
- [x] Error message templates for common cases
- [x] Code review checklist for error handling

**Frontend Error Handling Patterns:**
```javascript
// Always provide fallbacks
x-text="value || 'N/A'"
x-text="value ? value.toFixed(1) + '%' : 'N/A'"

// Check existence before operations
x-text="data?.field ? data.field.toUpperCase() : 'Unknown'"

// Track error state
data: [],
error: false,
errorMessage: '',
async loadData() {
    try {
        const response = await fetch('/api/data');
        if (!response.ok) throw new Error(`Server returned ${response.status}`);
        this.data = await response.json();
        this.error = false;
    } catch (e) {
        this.error = true;
        this.errorMessage = e.message || 'Unknown error';
    }
}
```

**Backend Error Handling Patterns:**
```python
# Specific status codes and context
raise HTTPException(
    status_code=404,
    detail=f"Node {node_id} not found. It may have been deleted."
)

# Include actionable information
raise HTTPException(
    status_code=503,
    detail=f"Cannot communicate with agent at {node_ip}. Agent may be offline."
)
```

### Roadmap Updates

**Phase 8: Fleet Management Added (commit `43c9c30`)**
- [ ] Remote agent code updates from web dashboard (one-click agent updates)
- [ ] Remote agent code updates via CLI (`nexus fleet update`, `nexus node update <node_id>`)
- [ ] Agent version tracking and update availability notifications
- [ ] Fleet-wide configuration management
- [ ] Bulk operations across multiple nodes (update all, restart all, etc.)
- [ ] Update rollback mechanism for failed updates
- [ ] Zero-downtime agent updates with graceful restarts

### Scripts & Tools

**Agent Update Script (commit `cfb0243`):**
- [x] Created `scripts/update-agent.sh`
  - Quick update for already-deployed agents
  - Stops agent, copies updated code, restarts
  - Preserves venv and configuration
  - Checks health after update
  - Faster than full redeployment

### Documentation Updates

- [x] API documentation updated (`docs/api.md`)
  - Added GET /api/nodes/{node_id}/disks endpoint
  - Included example response with disk type descriptions
- [x] README.md updated
  - Added reference to CONTRIBUTING.md
  - Marked Phase 7.2 as complete
  - Added Phase 8 roadmap
- [x] Error handling guidelines (`docs/CONTRIBUTING.md`) - NEW
  - Comprehensive development standards
  - Frontend and backend best practices
  - Testing checklists
  - Code review guidelines

### Git Commits (2025-12-02)

1. `6b980c0` - fix: Display numeric metrics in node health cards
2. `0b2f611` - fix: Add temperature card to health status display
3. `7e562bc` - fix: Correct health status value comparisons (lowercase)
4. `319f5e6` - feat: Add multi-disk display in node details view
5. `29e6fd5` - fix: Add proper error handling for storage devices section
6. `bbea328` - docs: Add comprehensive error handling guidelines
7. `cfb0243` - feat: Add quick agent update script
8. `43c9c30` - roadmap:- Or begin Phase 8: Remote fleet management and agent updates

---

## 🧹 Session: 2025-12-05 - State Verification

### Housekeeping
- **Verified Environment:**
  - Confirmed Core running on Linux Laptop (`10.243.99.44`)
  - Confirmed Agents on `moria-pi` and `Orthanc-pi`
  - Corrected documentation to remove checking "Windows" confusion
- **Documentation Updates:**
  - Updated `CONTEXT.md` with verified current state
  - Updated `PROGRESS.md` to reflect current maintenance status

### Testing Notes

**Live Testing on moria-pi:**
- ✅ Health status cards display correctly (CPU, Memory, Disk, Temp)
- ✅ Temperature sensor reading: 44-45°C (healthy range)
- ✅ Multi-disk detection working (requires agent update)
- ✅ Error handling provides clear, actionable messages
- ⚠️ Storage devices section awaiting agent update on moria-pi
  - Agent needs `/api/system/disks` endpoint (added in this session)
  - Update command: `./scripts/update-agent.sh 10.243.14.179 methinked 107512625`

### Key Achievements

1. **Zero "undefined" Errors:** Established and enforced standards to prevent undefined values in UI
2. **Complete Docker Orchestration:** Full container lifecycle management across fleet
3. **Multi-Disk Visibility:** Users can now see all storage devices with clear SD Card labels
4. **Developer Guidelines:** Comprehensive error handling documentation for all future development
5. **Remote Update Foundation:** Roadmap established for fleet-wide agent management

### Next Steps

**Immediate:**
- Update moria-pi agent to enable storage devices display
- Test multi-disk display with various storage configurations

**Phase 7.3: Docker Service Templates**
- Pre-built templates (Pi-hole, Home Assistant, Prometheus, etc.)
- Web UI enhancements for service deployment
- Docker Compose support

**Phase 8: Fleet Management**
- Design agent update protocol
- Implement version tracking
- Build one-click update interface

---

#### Phase 16: Stability - Automated Testing (In Progress) 🧪

- [x] **Test Infrastructure Setup**
  - Configured `pytest` with `asyncio` and `coverage`
  - Created test directory structure (`tests/core`, `tests/shared`, etc.)
  - Established `conftest.py` with scoped fixtures
  - Configured in-memory SQLite (`StaticPool`) for isolation
- [x] **Unit Testing Initialization**
  - Shared Models: 100% coverage for `nexus.shared.models`
  - Health Logic: 100% coverage for `nexus.core.services.health`
  - Verification of critical business logic (thresholds, validation)
- [x] **API Integration Testing**
  - Node API: CRUD operations verified
  - Auth API: Registration flow verified
  - Verified endpoints: List, Details, Updates, 404 handling
  - Found and fixed bugs in CRUD layer (Pydantic serialization issues)

**Current Status (2025-12-26):**
- Test Framework: **ACTIVE**
- Initial Coverage: ~24%
- Critical Paths Verified: Data Models, Health Calc, Node Management

---

## 📅 Roadmap Highlights

See [ROADMAP.md](ROADMAP.md) for full details.

### Immediate Focus
1.  **Phase 15: Security** (RBAC, TLS, Secure Token Handling)
2.  **Phase 4 (Refined):** Advanced Logs & Alerts
3.  **Phase 6 (Refined):** Dashboard "Day 2" Features
