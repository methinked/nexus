"""
Storage management and disk detection for Nexus Agent.

Provides multi-disk detection, type identification, and usage analysis.
"""

import logging
import os
from pathlib import Path
from typing import Optional

import psutil

from nexus.shared import DiskInfo, DiskType

logger = logging.getLogger(__name__)


def detect_disk_type(device: str) -> DiskType:
    """
    Detect the type of disk device (SD card, SSD, HDD, etc.).

    Args:
        device: Device path (e.g., /dev/sda, /dev/mmcblk0)

    Returns:
        DiskType enum value
    """
    device_name = Path(device).name

    # Remove partition numbers to get base device
    # /dev/sda1 -> /dev/sda, /dev/mmcblk0p1 -> /dev/mmcblk0
    if device_name.startswith("mmcblk"):
        base_device = device_name.split("p")[0]  # mmcblk0p1 -> mmcblk0
        # SD cards use mmcblk* devices
        return DiskType.SD_CARD
    elif device_name.startswith("nvme"):
        # NVMe SSDs
        return DiskType.NVME
    elif device_name.startswith("sd"):
        # SATA/USB devices (sda, sdb, etc.)
        base_device = device_name.rstrip("0123456789")  # sda1 -> sda

        # Try to determine if it's SSD or HDD
        try:
            # Check /sys/block/{device}/queue/rotational
            # 0 = SSD, 1 = HDD
            rotational_path = f"/sys/block/{base_device}/queue/rotational"
            if os.path.exists(rotational_path):
                with open(rotational_path, "r") as f:
                    rotational = int(f.read().strip())
                    if rotational == 0:
                        # Non-rotational = SSD
                        # Check if it's removable (USB)
                        removable_path = f"/sys/block/{base_device}/removable"
                        if os.path.exists(removable_path):
                            with open(removable_path, "r") as f:
                                removable = int(f.read().strip())
                                if removable == 1:
                                    # Could be USB flash or external SSD
                                    # Assume external SSD for now
                                    return DiskType.EXTERNAL_SSD
                        # Internal SSD or external via SATA
                        return DiskType.EXTERNAL_SSD
                    else:
                        # Rotational = HDD
                        return DiskType.EXTERNAL_HDD
        except (OSError, ValueError) as e:
            logger.debug(f"Could not determine disk type for {device}: {e}")

    # Default to unknown
    return DiskType.UNKNOWN


def check_docker_data_path(mount_point: str) -> bool:
    """
    Check if Docker data directory is on this mount point.

    Args:
        mount_point: Mount point to check

    Returns:
        True if Docker data is on this mount
    """
    # Common Docker data directories
    docker_dirs = [
        "/var/lib/docker",
        "/mnt/docker",
        "/data/docker",
        f"{mount_point}/docker",
    ]

    for docker_dir in docker_dirs:
        if os.path.exists(docker_dir) and os.path.ismount(docker_dir):
            # Check if docker_dir is under mount_point
            try:
                if os.path.commonpath([docker_dir, mount_point]) == mount_point:
                    return True
            except ValueError:
                # Paths on different drives
                continue

    return False


def check_nexus_data_path(mount_point: str) -> bool:
    """
    Check if Nexus data/logs are on this mount point.

    Args:
        mount_point: Mount point to check

    Returns:
        True if Nexus data is on this mount
    """
    # Check if data or logs directories are on this mount
    nexus_paths = [
        os.getenv("NEXUS_DATA_DIR", "data"),
        os.getenv("NEXUS_LOGS_DIR", "logs"),
    ]

    for nexus_path in nexus_paths:
        abs_path = os.path.abspath(nexus_path)
        if os.path.exists(abs_path):
            try:
                if os.path.commonpath([abs_path, mount_point]) == mount_point:
                    return True
            except ValueError:
                continue

    return False


def get_filesystem_label(device: str) -> Optional[str]:
    """
    Get the filesystem label for a device.

    Args:
        device: Device path

    Returns:
        Label string or None
    """
    try:
        # Try to read label from /dev/disk/by-label
        label_dir = Path("/dev/disk/by-label")
        if label_dir.exists():
            for label_path in label_dir.iterdir():
                if os.path.realpath(label_path) == device:
                    return label_path.name
    except (OSError, PermissionError):
        pass

    return None


def get_filesystem_uuid(device: str) -> Optional[str]:
    """
    Get the filesystem UUID for a device.

    Args:
        device: Device path

    Returns:
        UUID string or None
    """
    try:
        # Try to read UUID from /dev/disk/by-uuid
        uuid_dir = Path("/dev/disk/by-uuid")
        if uuid_dir.exists():
            for uuid_path in uuid_dir.iterdir():
                if os.path.realpath(uuid_path) == device:
                    return uuid_path.name
    except (OSError, PermissionError):
        pass

    return None


def get_all_disks() -> list[DiskInfo]:
    """
    Get information about all mounted disks.

    Returns:
        List of DiskInfo objects for all mounted disks
    """
    disks = []

    # Get all disk partitions
    partitions = psutil.disk_partitions(all=False)

    for partition in partitions:
        # Skip virtual filesystems
        if partition.fstype in ("tmpfs", "devtmpfs", "squashfs", "overlay", "proc", "sysfs", "devpts"):
            continue

        # Skip docker overlay mounts
        if "docker" in partition.mountpoint and "overlay" in partition.fstype:
            continue

        try:
            # Get disk usage
            usage = psutil.disk_usage(partition.mountpoint)

            # Detect disk type
            disk_type = detect_disk_type(partition.device)

            # Check if this is root filesystem
            is_system = partition.mountpoint == "/"

            # Check if Docker or Nexus data is on this disk
            is_docker = check_docker_data_path(partition.mountpoint)
            is_nexus = check_nexus_data_path(partition.mountpoint)

            # Check if read-only
            read_only = "ro" in partition.opts.split(",")

            # Get label and UUID
            label = get_filesystem_label(partition.device)
            uuid = get_filesystem_uuid(partition.device)

            # Create DiskInfo object
            disk_info = DiskInfo(
                device=partition.device,
                mount_point=partition.mountpoint,
                type=disk_type,
                filesystem=partition.fstype,
                total_bytes=usage.total,
                used_bytes=usage.used,
                free_bytes=usage.free,
                usage_percent=usage.percent,
                read_only=read_only,
                is_system=is_system,
                is_docker_data=is_docker,
                is_nexus_data=is_nexus,
                label=label,
                uuid=uuid,
            )

            disks.append(disk_info)

        except (PermissionError, OSError) as e:
            logger.warning(f"Could not get disk usage for {partition.mountpoint}: {e}")
            continue

    # Sort by mount point (root first, then alphabetically)
    disks.sort(key=lambda d: (not d.is_system, d.mount_point))

    return disks


def find_best_storage_disk(disks: list[DiskInfo]) -> Optional[DiskInfo]:
    """
    Find the best disk for Docker and logs (prefer external SSD).

    Priority:
    1. External SSD with > 50GB free
    2. External HDD with > 100GB free
    3. Root filesystem (fallback)

    Args:
        disks: List of available disks

    Returns:
        Best disk for storage, or None if only root available
    """
    # Minimum free space requirements (in bytes)
    MIN_SSD_FREE = 50 * 1024**3  # 50 GB
    MIN_HDD_FREE = 100 * 1024**3  # 100 GB

    # Filter out root filesystem and read-only disks
    external_disks = [d for d in disks if not d.is_system and not d.read_only]

    # Prefer external SSDs
    for disk in external_disks:
        if disk.type in (DiskType.EXTERNAL_SSD, DiskType.NVME):
            if disk.free_bytes >= MIN_SSD_FREE:
                return disk

    # Fall back to external HDDs
    for disk in external_disks:
        if disk.type == DiskType.EXTERNAL_HDD:
            if disk.free_bytes >= MIN_HDD_FREE:
                return disk

    # No suitable external disk found
    return None


def format_disk_size(bytes_value: int) -> str:
    """
    Format bytes as human-readable string.

    Args:
        bytes_value: Size in bytes

    Returns:
        Formatted string (e.g., "256 GB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"
