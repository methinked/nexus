# Manual Verification Strategy

This document outlines the manual testing procedures for the Nexus platform. Use this checklist to verify the system integrity before major releases or after significant refactoring.

## 1. Environment Setup
- [ ] **Core Server**: Ensure the Core server is running (`python -m nexus.core.main`).
- [ ] **Agents**: Ensure at least one agent is deployed and running.
- [ ] **Network**: Verify connectivity between Core and Agents (ping, curl).

## 2. Core Features Verification

### 2.1 Agent Registration
- [ ] **Startup**: Restart an agent and verify it appears in the `nexus node list` on the Core.
- [ ] **Identity**: Check that `node_id` persists across restarts (in `data/agent_state.json`).
- [ ] **Metadata**: Verify the agent reports correct hostname, OS, and IP address.

### 2.2 Metrics & Monitoring
- [ ] **Live Feed**: Open the Dashboard (`/`) and verify "Live Metrics" charts are updating every ~2-5 seconds (WebSocket).
- [ ] **Data Accuracy**: Run `htop` on the agent and compare CPU/RAM usage with the Dashboard.
- [ ] **Disconnection**: Stop the agent process. Verify the Dashboard shows the node as "Offline" (within ~60 seconds).
- [ ] **Reconnection**: Start the agent process. Verify it automatically reconnects and updates status to "Online".

### 2.3 Storage Detection (Phase 6.5.1)
- [ ] **Node Details**: Go to the Node Detail page.
- [ ] **Storage Panel**: Verify all mounted disks are listed.
- [ ] **Disk Types**: Check if SD Cards are correctly identified (vs SSD/HDD).
- [ ] **Usage**: Ensure disk usage bars match `df -h` on the agent.

## 3. Orchestration (Docker)

### 3.1 Service Templates
- [ ] **Listing**: Run `nexus service list` or view "Services" page in UI. Ensure seeded templates (Pi-hole, Home Assistant) are present.
- [ ] **Creation**: Create a dummy service template via UI/CLI.
- [ ] **Deletion**: Delete the dummy service template.

### 3.2 Deployment Lifecycle
- [ ] **Deploy**: Deploy a simple container (e.g., `nginx` or `hello-world`) to an agent.
    - Check "Deployments" page for status "Running".
    - Verify container is running on the agent (`docker ps`).
- [ ] **Stop**: Stop the deployment via UI/CLI.
    - Verify status "Stopped".
    - Check `docker ps -a` on agent.
- [ ] **Start**: Start the deployment again.
- [ ] **Logs**: View logs in the UI.
- [ ] **Remove**: Delete the deployment. Verify container is removed from agent.

## 4. Troubleshooting
- **Logs**: Check `core.log` and `agent.log` for Python tracebacks.
- **WebSocket**: Use browser DevTools (Network tab -> WS) to inspect `metric_update` messages.
- **API**: Use the CLI View in the Dashboard to inspect API calls and responses.
