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
    Check if Docker data directory is permanently stored on this mount point.
    
    This uses st_dev to verify the Docker root is physically on the same 
    device as the mount point, handling bind mounts and overlays correctly.

    Args:
        mount_point: Mount point to check

    Returns:
        True if Docker data is on this mount
    """
    # Get current Docker root
    docker_root = get_docker_root()

    if not docker_root:
        # Try default location
        docker_root = "/var/lib/docker"

    if not os.path.exists(docker_root):
        return False

    try:
        # Get device IDs
        docker_dev = os.stat(docker_root).st_dev
        mount_dev = os.stat(mount_point).st_dev
        
        # If devices match, Docker is stored here
        if docker_dev == mount_dev:
            return True
            
    except (OSError, ValueError):
        pass

    return False


def check_nexus_data_path(mount_point: str) -> bool:
    """
    Check if Nexus data/logs are stored on this mount point.

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

    try:
        mount_dev = os.stat(mount_point).st_dev
    except OSError:
        return False

    for nexus_path in nexus_paths:
        abs_path = os.path.abspath(nexus_path)
        if os.path.exists(abs_path):
            try:
                # Check if path is on same device
                path_dev = os.stat(abs_path).st_dev
                if path_dev == mount_dev:
                    return True
            except (OSError, ValueError):
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
    
    Filters out duplicates (bind mounts) by ensuring each unique physical 
    device is listed only once, prioritizing the root mount or the shortest path.

    Returns:
        List of DiskInfo objects for all mounted disks
    """
    disks = []
    seen_devices = set()
    candidate_partitions = []

    # Get all disk partitions
    partitions = psutil.disk_partitions(all=False)

    # First pass: Collect valid candidates
    for partition in partitions:
        # Skip virtual filesystems
        if partition.fstype in ("tmpfs", "devtmpfs", "squashfs", "overlay", "proc", "sysfs", "devpts"):
            continue

        # Skip docker overlay mounts
        if "docker" in partition.mountpoint and "overlay" in partition.fstype:
            continue

        candidate_partitions.append(partition)
    
    # Sort candidates to prioritize root '/' and shorter paths
    # This ensures that when we dedupe by device, we keep the most "main" mount point
    candidate_partitions.sort(key=lambda p: (p.mountpoint != '/', len(p.mountpoint)))

    for partition in candidate_partitions:
        try:
            # Skip if we've already seen this device (deduplication)
            # This handles bind mounts where the same device appears multiple times
            if partition.device in seen_devices:
                continue
                
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
            seen_devices.add(partition.device)

        except (PermissionError, OSError) as e:
            logger.warning(f"Could not get disk usage for {partition.mountpoint}: {e}")
            continue

    # Final sort: Root first, then alphabetical by mount point
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


# ============================================================================
# Docker Configuration
# ============================================================================

import json
import subprocess


def get_docker_root() -> Optional[str]:
    """
    Get current Docker root directory from daemon config.

    Returns:
        str: Docker root path or None if not configured
    """
    config_path = Path("/etc/docker/daemon.json")

    try:
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get("data-root")
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Failed to read Docker config: {e}")

    # Try to get from docker info
    try:
        result = subprocess.run(
            ["docker", "info", "--format", "{{.DockerRootDir}}"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return None


def configure_docker_storage(target_disk: DiskInfo) -> bool:
    """
    Configure Docker to use specified disk for storage.

    Args:
        target_disk: Disk to use for Docker storage

    Returns:
        bool: True if configuration successful
    """
    config_path = Path("/etc/docker/daemon.json")
    docker_root = f"{target_disk.mount_point}/docker"

    logger.info(
        f"Configuring Docker to use {docker_root} "
        f"({target_disk.type.value}, {format_disk_size(target_disk.free_bytes)} free)"
    )

    try:
        # Create Docker data directory
        docker_dir = Path(docker_root)
        docker_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created Docker directory: {docker_root}")

        # Read existing config or start fresh
        config = {}
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
            except json.JSONDecodeError:
                logger.warning("Existing daemon.json is invalid, creating new one")

        # Update data-root
        config["data-root"] = docker_root

        # Write config (requires sudo)
        config_str = json.dumps(config, indent=2)

        logger.info(f"Writing Docker daemon config: {config_str}")

        # Use sudo to write config
        result = subprocess.run(
            ["sudo", "tee", str(config_path)],
            input=config_str.encode(),
            capture_output=True,
            check=True
        )

        logger.info("Docker daemon configuration updated successfully")
        logger.warning(
            "Docker daemon restart required! Run: sudo systemctl restart docker"
        )

        return True

    except Exception as e:
        logger.error(f"Failed to configure Docker storage: {e}")
        return False


def restart_docker_daemon() -> bool:
    """
    Restart Docker daemon to apply configuration changes.

    Returns:
        bool: True if restart successful
    """
    try:
        logger.info("Restarting Docker daemon...")

        subprocess.run(
            ["sudo", "systemctl", "restart", "docker"],
            check=True,
            capture_output=True,
            timeout=30
        )

        logger.info("Docker daemon restarted successfully")
        return True

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logger.error(f"Failed to restart Docker daemon: {e}")
        return False


def setup_docker_storage_if_needed() -> Optional[DiskInfo]:
    """
    Detect storage and configure Docker if needed.

    This function:
    1. Detects all available disks
    2. Finds the best external storage (SSD/HDD)
    3. Configures Docker to use it if not already configured
    4. Returns the disk Docker is configured to use

    Returns:
        DiskInfo: Disk that Docker is using, or None if using default
    """
    logger.info("Checking Docker storage configuration...")

    # Get current Docker root
    current_root = get_docker_root()
    logger.info(f"Current Docker root: {current_root or 'default (/var/lib/docker)'}")

    # Detect all disks
    disks = get_all_disks()

    if not disks:
        logger.warning("No disks detected!")
        return None

    # Log detected disks
    logger.info(f"Detected {len(disks)} disk(s):")
    for disk in disks:
        logger.info(
            f"  {disk.device} ({disk.type.value}): {disk.mount_point} "
            f"- {format_disk_size(disk.free_bytes)} free"
        )

    # Find best external storage
    best_disk = find_best_storage_disk(disks)

    if not best_disk:
        # No external storage found, using SD card/root filesystem
        root_disk = next((d for d in disks if d.is_system), None)

        if root_disk and root_disk.type == DiskType.SD_CARD:
            logger.warning(
                "⚠️  NO EXTERNAL STORAGE DETECTED! ⚠️\n"
                "Docker is using the SD card. This will cause premature SD card failure.\n"
                "Please connect a USB drive or SSD for Docker storage."
            )

        return root_disk

    # Check if already configured correctly
    target_root = f"{best_disk.mount_point}/docker"

    if current_root == target_root:
        logger.info(f"Docker already configured for optimal storage: {target_root}")
        return best_disk

    # Configure Docker to use best disk
    logger.info(
        f"Configuring Docker to use {best_disk.type.value} at {best_disk.mount_point} "
        f"({format_disk_size(best_disk.free_bytes)} free)"
    )

    if configure_docker_storage(best_disk):
        logger.info("✅ Docker storage configured successfully")
        logger.warning("Docker daemon needs to be restarted for changes to take effect")
        return best_disk
    else:
        logger.error("Failed to configure Docker storage")
        return None
