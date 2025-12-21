"""
Shared Pydantic models for Nexus.

These models are used across Core, Agent, and CLI components for data validation
and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Enums
# ============================================================================


class NodeStatus(str, Enum):
    """Status of a node."""

    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"


class JobType(str, Enum):
    """Type of job to execute."""

    OCR = "ocr"
    SHELL = "shell"
    SYNC = "sync"
    UPDATE = "update"


class JobStatus(str, Enum):
    """Status of a job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class NodeHealth(str, Enum):
    """Health status of a node based on metrics."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertSeverity(str, Enum):
    """Severity level of an alert."""

    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Status of an alert."""

    ACTIVE = "active"
    RESOLVED = "resolved"


class AlertType(str, Enum):
    """Type of alert condition."""

    NODE_OFFLINE = "node_offline"
    HIGH_CPU = "high_cpu"
    HIGH_MEMORY = "high_memory"
    HIGH_DISK = "high_disk"
    HIGH_TEMP = "high_temp"





# ============================================================================
# Base Models
# ============================================================================


class TimestampedModel(BaseModel):
    """Base model with timestamp fields."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class BaseResponse(BaseModel):
    """Base response model."""

    message: Optional[str] = None


# ============================================================================
# Node Models
# ============================================================================


class NodeMetadata(BaseModel):
    """Metadata for a node."""

    location: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    description: Optional[str] = None
    # Inventory data (disks, containers)
    inventory: Dict[str, Any] = Field(default_factory=dict)
    # Extensible for custom fields
    custom: Dict[str, Any] = Field(default_factory=dict)


class NodeBase(BaseModel):
    """Base node model with common fields."""

    name: str = Field(..., min_length=1, max_length=100)
    ip_address: str
    metadata: NodeMetadata = Field(default_factory=NodeMetadata)


class NodeCreate(NodeBase):
    """Model for creating a new node (registration)."""

    shared_secret: str = Field(..., min_length=8)


class NodeUpdate(BaseModel):
    """Model for updating node information."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    metadata: Optional[NodeMetadata] = None


class Node(NodeBase, TimestampedModel):
    """Complete node model."""

    id: UUID = Field(default_factory=uuid4)
    status: NodeStatus = NodeStatus.OFFLINE
    last_seen: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class NodeWithMetrics(Node):
    """Node model with current metrics included."""

    current_metrics: Optional["MetricData"] = None
    active_jobs: int = 0


class NodeList(BaseModel):
    """Response model for listing nodes."""

    nodes: list[Node]
    total: int





# ============================================================================
# Job Models
# ============================================================================


class JobPayload(BaseModel):
    """Base payload for jobs - extensible for different job types."""

    # Common fields
    timeout: Optional[int] = Field(None, description="Timeout in seconds")

    # Extensible for job-specific fields
    data: Dict[str, Any] = Field(default_factory=dict)


class OCRJobPayload(JobPayload):
    """Payload for OCR jobs."""

    file_path: str
    language: str = "eng"
    output_format: str = "markdown"


class ShellJobPayload(JobPayload):
    """Payload for shell command jobs."""

    command: str
    working_dir: Optional[str] = None
    env: Dict[str, str] = Field(default_factory=dict)


class UpdateJobPayload(JobPayload):
    """Payload for update jobs."""

    version: str
    download_url: Optional[str] = None
    restart_service: bool = True


class JobCreate(BaseModel):
    """Model for creating a new job."""

    type: JobType
    node_id: UUID
    payload: Dict[str, Any]


class JobResult(BaseModel):
    """Result data from job execution."""

    success: bool = True
    output: Optional[str] = None
    error: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


class Job(TimestampedModel):
    """Complete job model."""

    id: UUID = Field(default_factory=uuid4)
    type: JobType
    node_id: UUID
    status: JobStatus = JobStatus.PENDING
    payload: Dict[str, Any]
    result: Optional[JobResult] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class JobList(BaseModel):
    """Response model for listing jobs."""

    jobs: list[Job]
    total: int


# ============================================================================
# Metric Models
# ============================================================================


class MetricData(BaseModel):
    """System metrics data."""

    cpu_percent: float = Field(..., ge=0, le=100)
    memory_percent: float = Field(..., ge=0, le=100)
    disk_percent: float = Field(..., ge=0, le=100)
    temperature: Optional[float] = Field(None, description="CPU temperature in Celsius")

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: Optional[float]) -> Optional[float]:
        """Validate temperature is within reasonable range."""
        if v is not None and (v < -50 or v > 150):
            raise ValueError("Temperature must be between -50 and 150 Celsius")
        return v


class MetricCreate(BaseModel):
    """Model for submitting metrics from agent."""

    node_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cpu_percent: float = Field(..., ge=0, le=100)
    memory_percent: float = Field(..., ge=0, le=100)
    disk_percent: float = Field(..., ge=0, le=100)
    temperature: Optional[float] = None


class Metric(TimestampedModel):
    """Complete metric model with storage timestamp."""

    id: UUID = Field(default_factory=uuid4)
    node_id: UUID
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    temperature: Optional[float] = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class MetricList(BaseModel):
    """Response model for listing metrics."""

    node_id: UUID
    metrics: list[Metric]


class MetricStats(BaseModel):
    """Aggregated statistics for metrics over a time period."""

    node_id: UUID
    start_time: datetime
    end_time: datetime
    count: int

    # CPU statistics
    cpu_avg: float
    cpu_min: float
    cpu_max: float

    # Memory statistics
    memory_avg: float
    memory_min: float
    memory_max: float

    # Disk statistics
    disk_avg: float
    disk_min: float
    disk_max: float

    # Temperature statistics (optional)
    temperature_avg: Optional[float] = None
    temperature_min: Optional[float] = None
    temperature_max: Optional[float] = None


class HealthThresholds(BaseModel):
    """Thresholds for determining node health status."""

    cpu_warning: float = 80.0
    cpu_critical: float = 95.0
    memory_warning: float = 85.0
    memory_critical: float = 95.0
    disk_warning: float = 85.0
    disk_critical: float = 95.0
    temperature_warning: Optional[float] = 75.0
    temperature_critical: Optional[float] = 85.0


class NodeHealthStatus(BaseModel):
    """Health status of a node with detailed breakdown."""

    node_id: UUID
    overall_health: NodeHealth
    last_check: datetime

    # Component health
    cpu_health: NodeHealth
    memory_health: NodeHealth
    disk_health: NodeHealth
    temperature_health: Optional[NodeHealth] = None

    # Latest metric values
    latest_metrics: Optional[Metric] = None

    # Thresholds used for calculation
    thresholds: HealthThresholds = Field(default_factory=HealthThresholds)


# ============================================================================
# Log Models
# ============================================================================


class LogLevel(str, Enum):
    """Log level."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogEntry(TimestampedModel):
    """Log entry from an agent."""

    id: UUID = Field(default_factory=uuid4)
    node_id: UUID
    level: LogLevel
    source: str  # Module/component name
    message: str
    extra: Dict[str, Any] = Field(default_factory=dict)  # Additional context

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class LogCreate(BaseModel):
    """Model for creating a log entry."""

    node_id: UUID
    level: LogLevel
    source: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    extra: Dict[str, Any] = Field(default_factory=dict)


class LogList(BaseModel):
    """Response model for listing logs."""

    logs: list[LogEntry]
    total: int


# ============================================================================
# Authentication Models
# ============================================================================


class TokenData(BaseModel):
    """Data contained in JWT token."""

    node_id: UUID
    node_name: str
    exp: Optional[datetime] = None


class Token(BaseModel):
    """JWT token response."""

    api_token: str
    token_type: str = "bearer"
    expires_at: datetime


class RegistrationRequest(NodeCreate):
    """Request model for node registration."""

    pass


class RegistrationResponse(BaseModel):
    """Response model for successful registration."""

    node_id: UUID
    api_token: str
    expires_at: datetime


# ============================================================================
# System Info Models
# ============================================================================


class SystemInfo(BaseModel):
    """System information from agent."""

    hostname: str
    os: str
    kernel: str
    architecture: str
    cpu_count: int
    total_memory: int = Field(..., description="Total memory in MB")
    total_disk: int = Field(..., description="Total disk in MB")





# ============================================================================
# Multi-Disk Storage Models (Phase 6.5)
# ============================================================================


class DiskType(str, Enum):
    """Disk device types for storage classification."""

    SD_CARD = "sd_card"
    EXTERNAL_SSD = "external_ssd"
    EXTERNAL_HDD = "external_hdd"
    NVME = "nvme"
    USB_FLASH = "usb_flash"
    UNKNOWN = "unknown"


class DiskInfo(BaseModel):
    """Information about a single disk/partition."""

    # Device identification
    device: str = Field(..., description="Device path (e.g., /dev/sda1)")
    mount_point: str = Field(..., description="Mount point (e.g., /mnt/external)")
    type: DiskType = Field(..., description="Disk device type")
    filesystem: str = Field(..., description="Filesystem type (e.g., ext4, vfat)")

    # Size information
    total_bytes: int = Field(..., description="Total disk space in bytes")
    used_bytes: int = Field(..., description="Used disk space in bytes")
    free_bytes: int = Field(..., description="Free disk space in bytes")
    usage_percent: float = Field(..., description="Usage percentage (0-100)")

    # Status flags
    read_only: bool = Field(default=False, description="Whether disk is mounted read-only")
    is_system: bool = Field(default=False, description="Whether this is the root filesystem")
    is_docker_data: bool = Field(default=False, description="Whether Docker data is on this disk")
    is_nexus_data: bool = Field(default=False, description="Whether Nexus data/logs are on this disk")

    # Optional metadata
    label: Optional[str] = Field(None, description="Disk label/name")
    uuid: Optional[str] = Field(None, description="Filesystem UUID")

    class Config:
        json_schema_extra = {
            "example": {
                "device": "/dev/sda1",
                "mount_point": "/mnt/external",
                "type": "external_ssd",
                "filesystem": "ext4",
                "total_bytes": 537696485376,
                "used_bytes": 243186032640,
                "free_bytes": 294510452736,
                "usage_percent": 45.2,
                "read_only": False,
                "is_system": False,
                "is_docker_data": True,
                "is_nexus_data": True,
                "label": "External SSD",
                "uuid": "abc123-def456"
            }
        }


class InventoryUpdate(BaseModel):
    """Inventory update from agent (Push model)."""

    node_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    disks: list[DiskInfo] = Field(default_factory=list)
    containers: list[Dict[str, Any]] = Field(default_factory=list)  # Using Dict for flexibility, can iterate to ContainerStatus


# ============================================================================
# Health Check Models
# ============================================================================


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "0.1.0"
    uptime: Optional[int] = Field(None, description="Uptime in seconds")
    node_id: Optional[UUID] = Field(None, description="For agent health checks")
    hostname: Optional[str] = Field(None, description="Hostname of the server")


# ============================================================================
# Error Models
# ============================================================================


class ErrorDetail(BaseModel):
    """Error detail information."""

    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: ErrorDetail


# ============================================================================
# Alert Models
# ============================================================================


class AlertBase(BaseModel):
    """Base alert model."""

    node_id: UUID
    type: AlertType
    severity: AlertSeverity
    message: str


class AlertCreate(AlertBase):
    """Model for creating a new alert."""
    pass


class AlertUpdate(BaseModel):
    """Model for updating an alert."""
    
    status: Optional[AlertStatus] = None
    resolved_at: Optional[datetime] = None


class Alert(AlertBase, TimestampedModel):
    """Complete alert model."""

    id: UUID = Field(default_factory=uuid4)
    status: AlertStatus = AlertStatus.ACTIVE
    resolved_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class AlertList(BaseModel):
    """Response model for listing alerts."""

    alerts: list[Alert]
    total: int


class NodeOverview(BaseModel):
    """Consolidated node details for UI optimization."""

    node_id: UUID
    health: NodeHealthStatus
    metrics: list["Metric"] = Field(default_factory=list)
    jobs: list["Job"] = Field(default_factory=list)
    logs: list["LogEntry"] = Field(default_factory=list)
    disks: list[DiskInfo] = Field(default_factory=list)
    containers: list[Dict[str, Any]] = Field(default_factory=list)

