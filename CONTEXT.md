# Nexus Project Context & Scope Lock

## 1. Project Philosophy
**"Lightweight Pi Fleet Observability & Telemetry"**

Nexus is a focused, agent-based system designed specifically for monitoring and managing home lab Raspberry Pi fleets.

**Core Focus:** "Visibility & telemetry, without the bloat."

We sit firmly in the Goldilocks zone:
- **Too Simple:** A static dashboard that just shows generic CPU usage.
- **Too Complex (REJECTED):** Full RMM tools, patch managers, Kubernetes, or bespoke Docker container orchestrators.

**What we ARE:**
- **Fleet Observer:** Real-time host telemetry (CPU, RAM, Temperatures, Storage classification, and failing SD card read-only detection).
- **Container Inspector:** Read-only visibility into Docker containers across nodes (uptime, port mappings, status).
- **Alert Engine:** Immediate warnings for host overheating, storage exhaustion, degraded filesystems, and node offline events.

**What we are NOT:**
- **Not an RMM:** No interactive shell proxies, no arbitrary script dispatchers, and no remote terminal backdoors.
- **Not a Patch Management Tool:** No bespoke binary OTA tarballs or package update pushers.
- **Not a Container Orchestrator:** No custom container schedulers or template deployment engines. Containers are managed natively via Docker Compose directly on each node.

---

## 🚫 The Anti-Creep Manifesto (Scope Lock)

1. **Observability First:** The agent exists to observe and report host and container health.
2. **No Custom Orchestration:** Do not re-introduce service templates, deployment lifecycles, or custom container runners.
3. **No Bespoke Patchers:** OS and package updates are handled via standard SSH/Ansible/apt, not pushed via Nexus agent jobs.
4. **Hardware Reality:** Always support physical Pi diagnostics (GPU temp via `vcgencmd`, disk classification, SD card read-only remount detection).
5. **CLI & Web Dual Interface:** Keep both the Typer CLI and Glassmorphic web dashboard clean, fast, and focused on telemetry.

---

## 🖥️ Fleet Nodes (Active State)

- **`orthanc-pi` (`192.168.1.222`):** Primary Core Server host + Docker stack (`jellyfin`, `pihole`, `meshcentral`, `unifi-controller`). Storage: NVMe.
- **`bywater-pi` (`192.168.1.175`):** Secondary node + Docker stack (`pihole`, `homecontrol`, `scriba`, `bootpc`). Reporting healthy telemetry every 30s.
- **`moria-pi` (`192.168.1.225`):** Offline / Maintenance backlog. Hardware failure: MicroSD card degraded into `read-only` state. (Replacement high-endurance SD card logged to master shopping/todo list).
