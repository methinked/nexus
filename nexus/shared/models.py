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


class DeploymentStatus(str, Enum):
    """Status of a service deployment."""

    DEPLOYING = "deploying"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    REMOVING = "removing"


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
# Service Models (Phase 7 - Docker Orchestration)
# ============================================================================


class ServiceBase(BaseModel):
    """Base service model with common fields."""

    name: str = Field(..., min_length=1, max_length=100, description="Unique service identifier")
    display_name: str = Field(..., min_length=1, max_length=200, description="Human-readable name")
    description: str = Field(..., description="Service description")
    version: str = Field(..., description="Service/image version")
    category: str = Field(default="general", description="Service category (networking, monitoring, etc.)")
    docker_compose: str = Field(..., description="Docker Compose YAML content")
    default_env: Dict[str, str] = Field(default_factory=dict, description="Default environment variables")
    icon_url: Optional[str] = Field(None, description="Icon URL for UI")


class ServiceCreate(ServiceBase):
    """Model for creating a new service template."""

    pass


class ServiceUpdate(BaseModel):
    """Model for updating a service template."""

    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    version: Optional[str] = None
    category: Optional[str] = None
    docker_compose: Optional[str] = None
    default_env: Optional[Dict[str, str]] = None
    icon_url: Optional[str] = None


class Service(ServiceBase, TimestampedModel):
    """Full service model with all fields."""

    id: UUID = Field(default_factory=uuid4)

    class Config:
        from_attributes = True


class ServiceList(BaseModel):
    """List of services."""

    services: list[Service]
    total: int


# ============================================================================
# Deployment Models (Phase 7 - Docker Orchestration)
# ============================================================================


class DeploymentConfig(BaseModel):
    """Configuration for a service deployment."""

    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    ports: Dict[str, str] = Field(default_factory=dict, description="Port mappings (host:container)")
    volumes: Dict[str, str] = Field(default_factory=dict, description="Volume mappings")
    networks: list[str] = Field(default_factory=list, description="Docker networks")
    restart_policy: str = Field(default="unless-stopped", description="Container restart policy")
    # Extensible for custom configuration
    custom: Dict[str, Any] = Field(default_factory=dict)


class DeploymentBase(BaseModel):
    """Base deployment model with common fields."""

    name: str = Field(..., min_length=1, max_length=100, description="User-defined deployment name")
    service_id: UUID = Field(..., description="Service template ID")
    node_id: UUID = Field(..., description="Target node ID")
    config: DeploymentConfig = Field(default_factory=DeploymentConfig, description="Deployment configuration")


class DeploymentCreate(DeploymentBase):
    """Model for creating a new deployment."""

    pass


class DeploymentUpdate(BaseModel):
    """Model for updating a deployment."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    config: Optional[DeploymentConfig] = None
    status: Optional[DeploymentStatus] = None


class Deployment(DeploymentBase, TimestampedModel):
    """Full deployment model with all fields."""

    id: UUID = Field(default_factory=uuid4)
    status: DeploymentStatus = Field(default=DeploymentStatus.DEPLOYING)
    container_id: Optional[str] = Field(None, description="Docker container ID from agent")
    deployed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeploymentList(BaseModel):
    """List of deployments."""

    deployments: list[Deployment]
    total: int


class DeploymentWithDetails(Deployment):
    """Deployment with related service and node information."""

    service: Optional[Service] = None
    node_name: Optional[str] = None
    node_ip: Optional[str] = None


# ============================================================================
# Container Status Models (Phase 7 - Docker Orchestration)
# ============================================================================


class ContainerStatus(BaseModel):
    """Container runtime status reported by agent."""

    deployment_id: UUID
    container_id: str
    status: str = Field(..., description="Container status (running, exited, paused, etc.)")
    cpu_percent: Optional[float] = Field(None, description="CPU usage percentage")
    memory_usage: Optional[int] = Field(None, description="Memory usage in bytes")
    created_at: datetime
    started_at: Optional[datetime] = None
    health: Optional[str] = Field(None, description="Health status (healthy, unhealthy, starting)")


# ============================================================================
# Health Check Models
# ============================================================================


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "0.1.0"
    uptime: Optional[int] = Field(None, description="Uptime in seconds")
    node_id: Optional[UUID] = Field(None, description="For agent health checks")


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
