# Nexus Roadmap & Planning

**Current Focus:** Stability, Testing, and Security (Phases 15-16)

## 📌 Project Status Overview
- **Core Functionality:** ✅ Complete (Agent Mesh, Metrics, Logs, Jobs, Docker Orchestration)
- **UI/UX:** ✅ Complete (Dashboard, Real-time Charts, Node Details)
- **Deployment:** ✅ Verified (3-Node Pi Fleet in Production)

## 🗺️ Active Roadmap

### 🔒 Phase 15: Security Hardening (Next Priority)
- [ ] **Strict TLS Enforcement**: Move all traffic to HTTPS.
- [ ] **Role-Based Access Control (RBAC)**: Admin vs View-Only users.
- [ ] **Secrets Management**: Replace `.env` with a secure vault (or encrypted secrets).

### 🛑 Phase 16: Stability Freeze & Testing
- [ ] **Automated Test Suite**:
    - [ ] Unit tests for Core Utils
    - [ ] Integration tests for Agent-Core communication
- [ ] **Memory Leak Analysis**: Long-term burn-in 7-day test.
- [ ] **Network Resilience**: Chaos monkey style network interruption tests.

### 🔮 Future Concepts (Parked)
- **Module System**: One-click install for complex apps (e.g., "Deploy Media Stack").
- **Vigil Legacy**: Scriptor (OCR) and Arbiter (Sync) - Low priority.

## 📝 Planning Audit (2025-12-26)
**Findings:**
1.  **Duplicate Roadmaps**: We had roadmaps in `README.md`, `CONTEXT.md`, and `PROGRESS.md`.
    *   *Action*: Consolidated high-level roadmap here. `PROGRESS.md` remains the historical log.
2.  **Test Records**: Testing was ad-hoc.
    *   *Action*: Established `docs/tests/` for verifiable audit trails.
3.  **Task Tracking**: Artifact `task.md` is ephemeral.
    *   *Action*: moving critical future tasks to this `ROADMAP.md` which lives in the repo.
