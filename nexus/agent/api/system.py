"""
System API routes for Nexus Agent.

Provides system information and status.
"""

import platform

from fastapi import APIRouter

from nexus.shared import SystemInfo

router = APIRouter()


@router.get("/info", response_model=SystemInfo)
async def get_system_info():
    """
    Get system information.

    Returns detailed information about the host system including
    OS, kernel, CPU, memory, and disk.

    TODO: Implement actual system info collection with psutil
    TODO: Handle Pi-specific info (vcgencmd for temperature)
    """
    # Basic platform info (works without psutil)
    info = SystemInfo(
        hostname=platform.node(),
        os=platform.system() + " " + platform.release(),
        kernel=platform.release(),
        architecture=platform.machine(),
        cpu_count=0,  # TODO: Use psutil.cpu_count()
        total_memory=0,  # TODO: Use psutil.virtual_memory().total
        total_disk=0,  # TODO: Use psutil.disk_usage('/').total
    )

    return info
