"""
System API routes for Nexus Agent.

Provides system information and status.
"""

import platform

import psutil
from fastapi import APIRouter

from nexus.agent.services.storage import get_all_disks
from nexus.shared import DiskInfo, SystemInfo

router = APIRouter()


@router.get("/info", response_model=SystemInfo)
async def get_system_info():
    """
    Get system information.

    Returns detailed information about the host system including
    OS, kernel, CPU, memory, and disk.
    """
    info = SystemInfo(
        hostname=platform.node(),
        os=platform.system() + " " + platform.release(),
        kernel=platform.release(),
        architecture=platform.machine(),
        cpu_count=psutil.cpu_count(logical=True),
        total_memory=psutil.virtual_memory().total,
        total_disk=psutil.disk_usage('/').total,
    )

    return info


@router.get("/disks", response_model=list[DiskInfo])
async def get_disk_info():
    """
    Get information about all mounted disks.

    Returns detailed information about each disk including:
    - Device path and mount point
    - Disk type (SD card, SSD, HDD, etc.)
    - Filesystem and usage statistics
    - Special flags (system, Docker data, Nexus data, read-only)
    """
    disks = get_all_disks()
    return disks
