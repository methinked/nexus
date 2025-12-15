
**Session 2025-12-14 (Monitoring MVP Complete):**
- **Legacy Cleanup:**
  - Removed "Service" and "Deployment" orchestration features (Routes, DB Models, CLI commands) to focus purely on monitoring.
- **Alert System Implemented:**
  - Real-time health monitoring for CPU (>95%), Memory (>95%), Disk (>95%), Temp (>85°C).
  - Node offline detection.
  - Interactive Alerts Modal on Dashboard.
- **Data Retention:**
  - Implemented 7-day metric retention policy to prevent database bloat.
  - Automatic background cleanup service.
- **Enhanced Inventory:**
  - Fixed "Black Hole" bug where container inventory was collected but dropped by API (Pydantic model fix).
  - Fixed Agent permissions for Docker socket.
  - Enhanced container data collection (Ports, Uptime, State).
  - Implemented "View Containers" modal for global fleet inventory.
- **Outcome:**
  - Nexus is now a robust, focused monitoring dashboard for the Raspberry Pi fleet.
  - "Orchestration" Pivot fully executed.
