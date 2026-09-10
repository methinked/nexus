from unittest.mock import patch, mock_open
from nexus.agent.services.storage import (
    detect_disk_type,
    format_disk_size,
    find_best_storage_disk
)
from nexus.shared.models import DiskInfo, DiskType

def test_format_disk_size():
    assert format_disk_size(500) == "500.0 B"
    assert format_disk_size(1024) == "1.0 KB"
    assert format_disk_size(1536) == "1.5 KB"
    assert format_disk_size(1024**2) == "1.0 MB"
    assert format_disk_size(1024**3) == "1.0 GB"
    assert format_disk_size(1024**4) == "1.0 TB"

def test_detect_disk_type_sd_card():
    assert detect_disk_type("/dev/mmcblk0") == DiskType.SD_CARD
    assert detect_disk_type("/dev/mmcblk0p1") == DiskType.SD_CARD

def test_detect_disk_type_nvme():
    assert detect_disk_type("/dev/nvme0n1") == DiskType.NVME
    assert detect_disk_type("/dev/nvme0n1p2") == DiskType.NVME

@patch("os.path.exists")
def test_detect_disk_type_unknown_sd(mock_exists):
    mock_exists.return_value = False
    assert detect_disk_type("/dev/sda") == DiskType.UNKNOWN

def test_find_best_storage_disk():
    # Empty list
    assert find_best_storage_disk([]) is None

    # Only root
    root_disk = DiskInfo(
        device="/dev/mmcblk0p2",
        mount_point="/",
        type=DiskType.SD_CARD,
        filesystem="ext4",
        total_bytes=1000,
        used_bytes=500,
        free_bytes=500,
        usage_percent=50.0,
        is_system=True
    )
    assert find_best_storage_disk([root_disk]) is None

    # SSD with enough space
    ssd_disk = DiskInfo(
        device="/dev/sda1",
        mount_point="/mnt/ssd",
        type=DiskType.EXTERNAL_SSD,
        filesystem="ext4",
        total_bytes=200 * 1024**3,
        used_bytes=50 * 1024**3,
        free_bytes=150 * 1024**3, # > 50GB
        usage_percent=25.0
    )
    assert find_best_storage_disk([root_disk, ssd_disk]) == ssd_disk

    # SSD with NOT enough space
    full_ssd = DiskInfo(
        device="/dev/sdb1",
        mount_point="/mnt/ssd2",
        type=DiskType.EXTERNAL_SSD,
        filesystem="ext4",
        total_bytes=200 * 1024**3,
        used_bytes=190 * 1024**3,
        free_bytes=10 * 1024**3, # < 50GB
        usage_percent=95.0
    )
    # Fallback to none since it doesn't have enough space and no HDD
    assert find_best_storage_disk([root_disk, full_ssd]) is None

    # HDD with enough space
    hdd_disk = DiskInfo(
        device="/dev/sdc1",
        mount_point="/mnt/hdd",
        type=DiskType.EXTERNAL_HDD,
        filesystem="ext4",
        total_bytes=1000 * 1024**3,
        used_bytes=500 * 1024**3,
        free_bytes=500 * 1024**3, # > 100GB
        usage_percent=50.0
    )
    assert find_best_storage_disk([root_disk, full_ssd, hdd_disk]) == hdd_disk
