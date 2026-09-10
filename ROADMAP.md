# Nexus Roadmap & Architecture Plan

**Scope Lock:** Lightweight Raspberry Pi Fleet Observability & Telemetry (No RMM / No Patch Management).

---

## 📌 Status & Milestones

### ✅ Phase 1: Fleet Triage & Host Hygiene (Completed)
- [x] Reclaimed 1.5 GB unrotated `agent.log` storage on Orthanc.
- [x] Normalized Git working tree (`core.filemode false`) resolving 100+ false-positive executable bit drifts.
- [x] Triaged `moria-pi` hardware fault (SD card failure remounted read-only); queued replacement high-endurance SD card to master todo & shopping lists.

### ✅ Phase 2: Codebase Pruning & Native ARM64 Toolchain (Completed)
- [x] Excised dead container orchestration & service template code (`deployments.py`, `services.py`, `seed_templates.py`, `service_templates.py`, `commands/deployment.py`, `commands/service.py`, `templates/deployments.html`, `templates/services.html`).
- [x] Removed flattened duplicate Python files from live deployment directory (`~/nexus-core/nexus/`).
- [x] Rebuilt native ARM64 virtual environment on Debian/Raspberry Pi OS, fixing x86 binary collision (`psutil.so`).
- [x] Automated test suite running 100% green across all units and integration tests.

### ✅ Phase 3: Documentation & Scope Realignment (Completed)
- [x] Rewrote `README.md` and `CONTEXT.md` to reflect true identity: Pi fleet observability and container visibility without RMM/patch management bloat.
- [x] Updated architecture documentation.

### 🚀 Phase 4: Unified Deployment Script (Next)
- [ ] Consolidate legacy 24 deployment/update scripts into a single, clean `deploy.sh` supporting:
  - Node target selection (`orthanc`, `bywater`, `moria`).
  - Automatic environment detection (LAN vs ZeroTier/Tailscale VPN).
  - Secure credential injection via `.env` instead of hardcoded passwords.
