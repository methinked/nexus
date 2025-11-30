"""
Shared configuration utilities for Nexus.

Uses pydantic-settings for environment-based configuration.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    """Base configuration shared across components."""

    model_config = SettingsConfigDict(
        env_prefix="NEXUS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    env: str = Field(default="development", description="Environment: development or production")
    log_level: str = Field(default="info", description="Logging level")

    # Security
    shared_secret: str = Field(
        default="change-me-in-production",
        description="Shared secret for agent registration",
    )

    # JWT Settings
    jwt_secret_key: str = Field(
        default="change-me-in-production-please",
        description="Secret key for JWT signing",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    jwt_expiration_hours: int = Field(default=24, description="JWT expiration time in hours")


class CoreConfig(BaseConfig):
    """Configuration for Core server."""

    # Server
    host: str = Field(default="0.0.0.0", description="Host to bind to")
    port: int = Field(default=8000, description="Port to bind to")

    # Database
    database_url: str = Field(
        default="sqlite:///data/nexus.db",
        description="Database connection URL",
    )

    # Log Retention
    log_retention_days: int = Field(
        default=7,
        description="Number of days to retain logs (0 = keep forever)",
    )
    log_cleanup_interval_hours: int = Field(
        default=24,
        description="How often to run log cleanup (in hours)",
    )

    # Paths
    data_dir: Path = Field(default=Path("data"), description="Data directory")
    logs_dir: Path = Field(default=Path("logs"), description="Logs directory")

    def __init__(self, **kwargs):
        """Initialize and create directories if they don't exist."""
        super().__init__(**kwargs)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


class AgentConfig(BaseConfig):
    """Configuration for Agent."""

    # Server
    host: str = Field(default="0.0.0.0", description="Host to bind to")
    port: int = Field(default=8001, description="Port to bind to")

    # Core connection
    core_url: str = Field(
        default="http://localhost:8000",
        description="URL of the Core server",
    )

    # Node identification
    node_name: str = Field(default="default-agent", description="Name of this agent node")
    node_id: Optional[str] = Field(default=None, description="UUID of this node (if registered)")

    # API Token (stored after registration)
    api_token: Optional[str] = Field(default=None, description="API token from Core")

    # Paths
    data_dir: Path = Field(default=Path("data"), description="Data directory")
    logs_dir: Path = Field(default=Path("logs"), description="Logs directory")
    sync_dir: Path = Field(default=Path("sync"), description="Syncthing sync directory")

    # Metrics collection
    metrics_interval: int = Field(default=30, description="Metrics collection interval in seconds")

    def __init__(self, **kwargs):
        """Initialize and create directories if they don't exist."""
        super().__init__(**kwargs)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.sync_dir.mkdir(parents=True, exist_ok=True)


class CLIConfig(BaseConfig):
    """Configuration for CLI."""

    # Core connection
    core_url: str = Field(
        default="http://localhost:8000",
        description="URL of the Core server",
    )

    # API Token (for authenticated requests)
    api_token: Optional[str] = Field(default=None, description="API token for CLI")

    # Output format
    output_format: str = Field(default="rich", description="Output format: rich, json, plain")
