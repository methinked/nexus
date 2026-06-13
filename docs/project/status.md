# Nexus Project Status

**Last Updated:** 2026-03-14
**Current Phase:** Production Maintenance & Monitoring

---

## 🚀 Project Overview

Nexus is a lightweight fleet management and observability system for home lab environments, specifically designed for Raspberry Pi nodes. The system provides "Single Pane of Glass" visibility into fleet health with CPU, RAM, temperature, and storage monitoring, plus standardized Docker service deployment capabilities.

**Core Philosophy:** "Visibility & Control, without the bloat" - positioned between static dashboards and complex orchestration platforms like Kubernetes.

---

## 📊 Current Fleet Status

### Active Nodes
- **Orthanc-pi** ✅: Primary Core Server & Agent. Online and fully operational.
  - Location: ZeroTier (10.243.151.228)
  - Role: Core server, metrics collection, job execution
  - Last seen: 2026-03-14T14:41:56

- **Bywater-pi** ✅: Remote Agent. Online and reporting metrics.
  - Location: LAN (192.168.1.100)
  - Role: Metrics collection, job execution
  - Last seen: 2026-03-14T14:42:02

- **Moria-pi** ❌: Raspberry Pi 3 Model B - SD Card Failure (offline, needs repair).
  - Location: LAN (192.168.1.225)
  - Status: Offline since SD card failure
  - Last seen: 2025-12-26

**Fleet Health:** 2/3 nodes operational (66.7% uptime)

---

## ✅ Completed Phases

### Phase 0: Project Initialization (Complete ✓)
- Repository setup, documentation structure, Docker configuration
- Development tooling and environment setup

### Phase 1: The Bedrock (Complete ✓)
- Shared models, config, and auth utilities
- Core and Agent FastAPI skeletons
- CLI foundation with Typer

### Phase 1.5: Database Layer (Complete ✓)
- SQLAlchemy models and CRUD operations
- Alembic migrations for SQLite database

### Phase 2: The Mesh - Agent Connectivity (Complete ✓)
- Agent registration and JWT authentication
- Real metrics collection with psutil
- End-to-end testing with live data

### Phase 3: The Pulse - Metrics Visualization (Complete ✓)
- Health calculation service with thresholds
- CLI metrics commands with rich formatting

### Phase 4: The Brain - Logging & Remote Control (Complete ✓)
- Centralized logging system with database storage
- Agent log collection and batch sending
- CLI logs viewer with filtering and tail mode
- Terminal WebSocket infrastructure (deferred implementation)

### Phase 5: The Hands - Workload Orchestration (Complete ✓)
- Job execution architecture with queue-based system
- Shell executor for command execution
- Job dispatcher service with background processing

### Phase 6: The Dashboard - Visualization & Monitoring (Complete ✓)
- Web dashboard with purple dark theme
- Real-time metrics charts with Chart.js
- Node detail views with comprehensive information
- WebSocket real-time updates
- Jobs management UI
- Logs viewer UI

### Phase 7: Docker Orchestration (Removed - Project Pivot)
- Originally planned for service management, but removed to maintain lightweight focus
- Core API and database models were implemented but removed from active development

### Phase 8-12: UI/UX Refinements (Complete ✓)
- Chart.js refactoring and performance optimizations
- Service visibility enhancements
- System reliability improvements
- Developer features and stats views

### Phase 13: Agent Auto-Update & Resilience (Complete ✓)
- Remote self-updating mechanism
- Core update orchestration
- Dashboard integration
- Re-registration support and crash fixes

### Phase 14: Fleet Maintenance (Complete ✓)
- Agent update mechanisms
- Self-diagnostics and error reporting

---

## 🔧 Critical Incidents (Resolved)

### Orthanc-Pi Controller Instance Fix (2026-03-14)
**Issue:** Malformed CORE_URL configuration causing agent startup failure
**Resolution:** Corrected URL and restarted service
**Status:** ✅ RESOLVED - Full fleet operational

---

## 📋 Current Phase: Production Maintenance & Monitoring

**Goal:** Maintain stable production operation of the fleet with monitoring and maintenance capabilities.

**Active Tasks:**
- Monitor fleet health and metrics
- Handle agent updates and maintenance
- Address any production issues promptly
- Plan future enhancements based on usage feedback

---

## 🔮 Future Roadmap

### Phase 15: Security Hardening
- Strict TLS enforcement
- Role-based access control (Admin vs View-Only)

### Phase 16: Stability Freeze
- Comprehensive test suite
- Long-term memory leak testing
- Performance tuning

### Potential Future Enhancements
- Mobile-responsive dashboard improvements
- Enhanced container detection
- Template versioning for services (if Docker orchestration reintroduced)

---

## 🏗️ System Architecture

- **Core Server:** FastAPI application with SQLite database
- **Agent:** Lightweight FastAPI clients on each node
- **CLI:** Typer-based command-line interface
- **Web Dashboard:** HTMX + Alpine.js + Tailwind CSS
- **Communication:** REST APIs with JWT authentication
- **Real-time Updates:** WebSocket for live metrics

---

## 📈 Key Metrics

- **Codebase:** ~10,000 lines across Core, Agent, CLI, and Web components
- **Fleet Size:** 3 Raspberry Pi nodes (2 currently operational)
- **Uptime:** High availability with automatic recovery
- **Performance:** Sub-second response times, 30-second metric intervals

---

## 🔗 Quick Links

- [README.md](README.md) - Project overview and getting started
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture details
- [docs/api.md](docs/api.md) - Complete API documentation
- [ROADMAP.md](ROADMAP.md) - Detailed development roadmap
- [CONTEXT.md](CONTEXT.md) - Project philosophy and guidelines</content>
<parameter name="filePath">/home/methinked/Projects/nexus/nexus/STATUS.md