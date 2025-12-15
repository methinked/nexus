"""
SQLAlchemy ORM models for Nexus Core database.

Defines database schema for nodes, jobs, and metrics.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from nexus.core.db.database import Base
from nexus.shared.models import JobStatus, JobType, NodeStatus


def generate_uuid() -> str:
    """Generate a UUID string for primary keys."""
    return str(uuid.uuid4())


class NodeModel(Base):
    """Node database model."""

    __tablename__ = "nodes"

    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Core fields
    name = Column(String(100), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)  # Support IPv6
    status = Column(Enum(NodeStatus), default=NodeStatus.OFFLINE, nullable=False, index=True)

    # Metadata (stored as JSON) - use node_metadata to avoid conflict with Base.metadata
    node_metadata = Column("metadata", JSON, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_seen = Column(DateTime, nullable=True)

    # Relationships
    jobs = relationship("JobModel", back_populates="node", cascade="all, delete-orphan")
    metrics = relationship("MetricModel", back_populates="node", cascade="all, delete-orphan")
    logs = relationship("LogModel", back_populates="node", cascade="all, delete-orphan")
    alerts = relationship("AlertModel", back_populates="node", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Node(id={self.id}, name={self.name}, status={self.status})>"


class JobModel(Base):
    """Job database model."""

    __tablename__ = "jobs"

    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Core fields
    type = Column(Enum(JobType), nullable=False, index=True)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)

    # Foreign key to node
    node_id = Column(String(36), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True)

    # Job data (stored as JSON)
    payload = Column(JSON, default=dict, nullable=False)
    result = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    node = relationship("NodeModel", back_populates="jobs")

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, type={self.type}, status={self.status}, node_id={self.node_id})>"


class MetricModel(Base):
    """Metric database model."""

    __tablename__ = "metrics"

    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Foreign key to node
    node_id = Column(String(36), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True)

    # Metric data
    timestamp = Column(DateTime, nullable=False, index=True)
    cpu_percent = Column(Float, nullable=False)
    memory_percent = Column(Float, nullable=False)
    disk_percent = Column(Float, nullable=False)
    temperature = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    node = relationship("NodeModel", back_populates="metrics")

    def __repr__(self) -> str:
        return f"<Metric(id={self.id}, node_id={self.node_id}, timestamp={self.timestamp})>"


class LogModel(Base):
    """Log entry database model."""

    __tablename__ = "logs"

    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Foreign key to node
    node_id = Column(String(36), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True)

    # Log data
    timestamp = Column(DateTime, nullable=False, index=True)
    level = Column(String(20), nullable=False, index=True)  # debug, info, warning, error, critical
    source = Column(String(255), nullable=False, index=True)  # Module/component name
    message = Column(Text, nullable=False)
    extra = Column(JSON, nullable=True)  # Additional context as JSON

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    node = relationship("NodeModel", back_populates="logs")

    def __repr__(self) -> str:
        return f"<Log(id={self.id}, node_id={self.node_id}, level={self.level}, source={self.source})>"


class AlertModel(Base):
    """Alert database model."""

    __tablename__ = "alerts"

    # Primary key
    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Foreign key to node
    node_id = Column(String(36), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True)

    # Alert details
    type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), default="active", nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    node = relationship("NodeModel", back_populates="alerts")

    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, node_id={self.node_id}, type={self.type}, status={self.status})>"




