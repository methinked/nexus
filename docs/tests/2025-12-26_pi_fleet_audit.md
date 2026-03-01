# Test Environment Audit: The Pi Fleet
**Date:** 2026-02-28 (Updated)  
**Controller:** 10.243.151.228 (Orthanc-Pi)  
**Total Nodes:** 3 (2 Active, 1 Offline)

## 1. Environment Overview
The test environment consists of 3 Raspberry Pi nodes connected via a mix of local LAN (`192.168.1.x`) and ZeroTier VPN (`10.243.x.x`).

| Hostname | Role | IP (LAN) | IP (Next) | Hardware | Storage | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **orthanc-pi** | Core + Agent | `192.168.1.222` | `10.243.151.228`| Pi 5 (NVMe) | NVMe SSD | ✅ Online |
| **bywater-pi** | Agent | `192.168.1.175` | - | Pi 4 | **SD Card (Risk)** | ✅ Online |
| **moria-pi** | Former Core | `192.168.1.225` | `10.243.14.179` | Pi 3B+ | SD Card | ❌ Offline (Failed) |

## 2. Node Functionality & Status

### 2.1 Orthanc-Pi (The New Core)
- **Function**: Runs the Nexus Core server and an Agent.
- **Functionality**:
    - Core API accessible at `http://10.243.151.228:8000`.
    - Agent metrics reporting correctly.
    - Hosting Docker containers: `pihole`, `unifi-controller`.
- **Storage**: NVMe SSD (`/dev/nvme0n1p2`). **Excellent.**
- **Issues**: None.

### 2.2 Bywater-Pi (The Risk)
- **Function**: Standard Agent node.
- **Functionality**:
    - Agent metrics reporting correctly.
    - Hosting Docker containers: `scriba`, `bootpc`.
- **Storage**: Docker root is on **SD Card** (`/dev/mmcblk0p2`).
    - **CRITICAL**: High risk of SD card corruption due to Docker write cycles.
- **Issues**: Using SD card for Docker storage.

### 2.3 Moria-Pi (Offline)
- **Function**: Former Core + Agent node.
- **Functionality**:
    - Offline permanently for foreseeable future due to SD card logic failure/corruption.
- **Storage**: SD Card `/dev/mmcblk0`
- **Issues**: Catastrophic SD card failure leading to retirement from active duty.

## 3. Problems & Risks
1.  **SD Card Usage (Bywater)**: `bywater-pi` is running Docker on its SD card. This is a known failure point.
2.  **Network Complexity**: Mixed usage of LAN IPs (`192.168.1.x`) and ZeroTier IPs (`10.243.x.x`) in configuration/logs can be confusing.
3.  **Authentication**: SSH access relies on a shared `TempSSHForTesting.txt` file. We need to verify who has access to these keys.

## 4. Future Plans
- [ ] **Migrate Bywater Storage**: Move `bywater-pi` Docker root to external USB storage.
- [ ] **Standardize Networking**: Decide on a primary interface (LAN vs ZeroTier) for inter-node communication.
- [ ] **Automated Testing**: Use this fleet for automated regression testing (e.g., deploying a test container to all 3 nodes).
