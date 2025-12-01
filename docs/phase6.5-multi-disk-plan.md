# Phase 6.5: Multi-Disk Storage Support - Implementation Plan

**Version:** 1.0
**Date:** 2025-12-01
**Status:** Planning Phase

---

## 🎯 Overview

Raspberry Pis often have multiple storage devices (SD card + external USB drives/SSDs). Nexus needs to:
1. **Detect and monitor all disks** - Not just root filesystem
2. **Prefer external storage** - Automatically use SSDs/USB drives for Docker and logs
3. **Visualize disk topology** - Show users which disk is used for what
4. **Warn about SD card usage** - Alert if critical writes happening to SD card

**Why This Matters:**
- SD cards fail quickly under Docker's constant writes (~10k-100k write cycles)
- External SSDs are 10x more reliable for databases, containers, and logs
- Users need visibility into storage health across multiple devices
- Production Pi deployments require smart storage management

---

## 🏗️ Architecture

### Current State
```python
# Single disk metric
{
    "disk_percent": 14.4,  # Only tracks root filesystem
    "temperature": 45.1
}
```

### Target State
```python
# Multi-disk metrics
{
    "disks": [
        {
            "device": "/dev/mmcblk0p2",
            "mount_point": "/",
            "type": "sd_card",
            "filesystem": "ext4",
            "total_bytes": 32010928128,
            "used_bytes": 4611686400,
            "free_bytes": 27399241728,
            "usage_percent": 14.4,
            "read_only": false,
            "is_system": true
        },
        {
            "device": "/dev/sda1",
            "mount_point": "/mnt/external",
            "type": "external_ssd",
            "filesystem": "ext4",
            "total_bytes": 537696485376,
            "used_bytes": 243186032640,
            "free_bytes": 294510452736,
            "usage_percent": 45.2,
            "read_only": false,
            "is_docker_data": true,
            "is_nexus_data": true
        }
    ],
    "temperature": 45.1
}
```

---

## 📋 Data Models

### Disk Information Model (Pydantic)

```python
class DiskType(str, Enum):
    """Disk device types"""
    SD_CARD = "sd_card"
    EXTERNAL_SSD = "external_ssd"
    EXTERNAL_HDD = "external_hdd"
    NVME = "nvme"
    USB_FLASH = "usb_flash"
    UNKNOWN = "unknown"

class DiskInfo(BaseModel):
    """Information about a single disk/partition"""
    device: str  # e.g., "/dev/sda1"
    mount_point: str  # e.g., "/mnt/external"
    type: DiskType
    filesystem: str  # e.g., "ext4", "vfat"

    # Size information
    total_bytes: int
    used_bytes: int
    free_bytes: int
    usage_percent: float

    # Flags
    read_only: bool = False
    is_system: bool = False  # Root filesystem
    is_docker_data: bool = False  # Docker data directory
    is_nexus_data: bool = False  # Nexus logs/database

    # Optional metadata
    label: Optional[str] = None
    uuid: Optional[str] = None

class NodeMetricsWithDisks(BaseModel):
    """Extended metrics model with multi-disk support"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    temperature: Optional[float] = None

    # Multi-disk metrics
    disks: list[DiskInfo] = []

    # Legacy single-disk for backward compatibility
    disk_percent: Optional[float] = None  # Deprecated: use disks[0].usage_percent
```

---

## 🔧 Implementation Tasks

### Phase 6.5.1: Agent Disk Detection (2-3 hours)

**Goal:** Detect all mounted disks and identify their types

**Tasks:**
1. **Disk enumeration:**
   - Use `psutil.disk_partitions(all=False)` to get all mounted partitions
   - Filter out virtual filesystems (tmpfs, devtmpfs, etc.)
   - Identify device types (SD vs USB vs SSD)

2. **Device type detection:**
   ```python
   def detect_disk_type(device: str) -> DiskType:
       """Detect if disk is SD card, SSD, HDD, etc."""
       # Check /sys/block/{device}/removable
       # Check /sys/block/{device}/queue/rotational
       # Check device name patterns (mmcblk* = SD, sd* = USB/SATA)
   ```

3. **Usage analysis:**
   ```python
   def analyze_disk_usage(mount_point: str) -> dict:
       """Determine what's using this disk"""
       # Check if Docker data dir is on this mount
       # Check if Nexus data dir is on this mount
       # Check if it's root filesystem
   ```

4. **Integration with MetricsCollector:**
   - Update `collect_metrics()` to gather multi-disk data
   - Maintain backward compatibility (set `disk_percent` from root disk)

**Files to modify:**
- `nexus/agent/services/metrics.py`
- `nexus/shared/models.py` (add DiskInfo, DiskType)

---

### Phase 6.5.2: Database Schema Extension (1-2 hours)

**Goal:** Store multi-disk metrics in database

**Options:**

**Option A: JSON in existing metrics table (Quick)**
- Add `disks_json` column to MetricModel
- Store serialized list of DiskInfo
- Pro: No migration complexity
- Con: Harder to query per-disk

**Option B: Separate disks table (Proper)**
- Create `disk_metrics` table with one row per disk per timestamp
- Foreign key to metrics table
- Pro: Queryable, relational
- Con: More complex queries

**Recommendation:** Start with Option A, migrate to Option B if needed.

**Tasks:**
1. Add `disks_json` column to MetricModel (nullable, JSON type)
2. Update CRUD to serialize/deserialize disk info
3. Create Alembic migration
4. Update API to return disk data

**Files to modify:**
- `nexus/core/db/models.py`
- `nexus/core/db/crud.py`
- `alembic/versions/` (new migration)

---

### Phase 6.5.3: Smart Storage Placement (2-3 hours)

**Goal:** Automatically use external disks for Docker and logs

**Tasks:**
1. **External disk detection on agent startup:**
   ```python
   def find_best_storage_disk() -> Optional[Path]:
       """Find best disk for Docker/logs (prefer external SSD)"""
       disks = get_all_disks()

       # Priority:
       # 1. External SSD with > 50GB free
       # 2. External HDD with > 100GB free
       # 3. Root filesystem (fallback, warn user)
   ```

2. **Configuration setup:**
   ```python
   def configure_storage_paths(config: AgentConfig):
       """Set Docker and Nexus data paths"""
       best_disk = find_best_storage_disk()

       if best_disk and best_disk.mount != "/":
           # Use external disk
           config.docker_data_dir = best_disk.mount / "docker"
           config.nexus_data_dir = best_disk.mount / "nexus/data"
           config.nexus_logs_dir = best_disk.mount / "nexus/logs"
       else:
           # Warn: Using SD card
           logger.warning("No external disk found, using SD card (not recommended)")
   ```

3. **Docker daemon configuration:**
   - Agent creates/updates `/etc/docker/daemon.json` if needed
   - Sets `data-root` to external disk
   - Requires Docker restart (agent can suggest, not auto-restart)

4. **Migration support:**
   - If Docker already has data on SD card, suggest migration
   - Provide CLI command to migrate: `nexus migrate-docker-data`

**Files to create/modify:**
- `nexus/agent/services/storage.py` (new)
- `nexus/agent/main.py` (call on startup)
- `nexus/shared/config.py` (add storage config fields)

---

### Phase 6.5.4: Dashboard Multi-Disk UI (3-4 hours)

**Goal:** Display all disks clearly in node detail view

**UI Design:**

```
┌─────────────────────────────────────────────────────────┐
│ Storage (2 disks)                                       │
├─────────────────────────────────────────────────────────┤
│ 💾 SD Card (System)                                     │
│ /dev/mmcblk0p2 → /                                      │
│ [████░░░░░░░░░░░░░░░░] 14.4% (4.3 GB / 29.8 GB)        │
│ ext4 • System only                                      │
│ ⚠️  Avoid heavy writes to SD card                       │
├─────────────────────────────────────────────────────────┤
│ 💿 External SSD                                         │
│ /dev/sda1 → /mnt/external                               │
│ [████████████░░░░░░░░] 45.2% (226 GB / 500 GB)         │
│ ext4 • Docker data • Nexus logs                         │
│ ✓ Optimal for containers and databases                  │
└─────────────────────────────────────────────────────────┘
```

**Tasks:**
1. Create disk visualization component
2. Color-code by type (SD = amber, SSD = green)
3. Show warnings if Docker on SD card
4. Add disk usage charts (per-disk over time)
5. Tooltip with mount details

**Files to modify:**
- `nexus/web/templates/nodes.html`
- `nexus/web/static/styles.css` (disk badges)

---

### Phase 6.5.5: Alerts and Best Practices (1-2 hours)

**Goal:** Warn users about suboptimal configurations

**Alerts:**
1. **Docker on SD card:** "Docker is using SD card storage. This can cause premature SD card failure. Consider moving to external SSD."
2. **Logs on SD card:** "Nexus logs are being written to SD card. For better reliability, use external storage."
3. **High SD card usage:** "SD card is >80% full. Consider using external storage for large files."
4. **No external disk detected:** "No external storage detected. For production use, attach an SSD via USB."

**Best Practices Documentation:**
- How to mount external disk on Raspberry Pi
- How to migrate Docker data to external disk
- Recommended external SSDs for Pi
- Performance comparison (SD vs USB 3.0 SSD)

**Files to create:**
- `docs/best-practices-storage.md`
- Alert logic in Core or Agent

---

## 🧪 Testing Strategy

### Unit Tests
- Disk type detection logic
- Storage path selection
- Disk metrics collection

### Integration Tests
- Multi-disk metrics submission to Core
- Database storage and retrieval
- API endpoints returning disk data

### Real-World Testing
- Test on Pi with only SD card
- Test on Pi with SD + USB SSD
- Test on Pi with SD + multiple USB drives
- Verify Docker migration process

---

## 📊 Success Metrics

Phase 6.5 is successful if:
1. ✅ All mounted disks visible in node detail view
2. ✅ Agent automatically uses external SSD for Docker if available
3. ✅ Users warned if Docker running on SD card
4. ✅ Per-disk usage charts working
5. ✅ Storage migration documented and tested
6. ✅ Works on Pis with 1-5+ disks

---

## 🔄 Backward Compatibility

- Keep `disk_percent` field in metrics for existing dashboards
- Set `disk_percent` to root filesystem usage
- Gradually deprecate single-disk field over 2-3 releases
- Old agents without multi-disk support still work

---

## 📝 Documentation Needs

1. **User Guide:**
   - How to attach external SSD to Pi
   - How to mount disk on boot (/etc/fstab)
   - How to migrate Docker data

2. **Admin Guide:**
   - Storage best practices
   - Recommended hardware (USB 3.0 SSDs)
   - Performance tuning

3. **API Reference:**
   - New disk metrics endpoints
   - DiskInfo model specification

---

## 🎯 Implementation Order

**Week 1:**
- Day 1-2: Phase 6.5.1 - Agent disk detection
- Day 2-3: Phase 6.5.2 - Database schema
- Day 3-4: Phase 6.5.3 - Smart storage placement
- Day 5: Testing and bug fixes

**Week 2:**
- Day 1-3: Phase 6.5.4 - Dashboard UI
- Day 4: Phase 6.5.5 - Alerts and docs
- Day 5: End-to-end testing on real Pi

**Total Estimated Effort:** 2 weeks

---

## 💡 Future Enhancements (Post-6.5)

- **Disk health monitoring** - SMART data, wear indicators
- **Automatic disk migration** - One-click Docker data migration
- **Disk performance metrics** - Read/write IOPS, latency
- **Storage pools** - Combine multiple disks (RAID, LVM)
- **Backup to external disk** - Automatic Nexus database backups

---

**End of Phase 6.5 Planning Document**
