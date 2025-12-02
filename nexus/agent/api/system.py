"""
System API routes for Nexus Agent.

Provides system information and status.
"""

import platform

import psutil
from fastapi import APIRouter

from nexus.shared import SystemInfo

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
