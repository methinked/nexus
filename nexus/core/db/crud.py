"""
CRUD operations for database models.

Provides create, read, update, and delete operations for nodes, jobs, and metrics.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from nexus.core.db.models import JobModel, MetricModel, NodeModel
from nexus.shared.models import (
    JobCreate,
    JobStatus,
    JobType,
    MetricCreate,
    NodeCreate,
    NodeStatus,
    NodeUpdate,
)


# ============================================================================
# Node CRUD Operations
# ============================================================================


def create_node(db: Session, node: NodeCreate) -> NodeModel:
    """Create a new node."""
    db_node = NodeModel(
        name=node.name,
        ip_address=node.ip_address,
        status=NodeStatus.ONLINE,
        node_metadata=node.metadata.model_dump(),
        last_seen=datetime.utcnow(),
    )
    db.add(db_node)
    db.commit()
    db.refresh(db_node)
    return db_node


def get_node(db: Session, node_id: str) -> Optional[NodeModel]:
    """Get a node by ID."""
    return db.query(NodeModel).filter(NodeModel.id == node_id).first()


def get_node_by_name(db: Session, name: str) -> Optional[NodeModel]:
    """Get a node by name."""
    return db.query(NodeModel).filter(NodeModel.name == name).first()


def get_nodes(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[NodeStatus] = None,
) -> List[NodeModel]:
    """Get all nodes with optional filtering."""
    query = db.query(NodeModel)

    if status:
        query = query.filter(NodeModel.status == status)

    return query.offset(skip).limit(limit).all()


def get_nodes_count(db: Session, status: Optional[NodeStatus] = None) -> int:
    """Get total count of nodes with optional filtering."""
    query = db.query(NodeModel)

    if status:
        query = query.filter(NodeModel.status == status)

    return query.count()


def update_node(db: Session, node_id: str, node_update: NodeUpdate) -> Optional[NodeModel]:
    """Update a node."""
    db_node = get_node(db, node_id)
    if not db_node:
        return None

    update_data = node_update.model_dump(exclude_unset=True)

    # Handle metadata separately - map to node_metadata field
    if "metadata" in update_data:
        update_data["node_metadata"] = update_data.pop("metadata").model_dump()

    for field, value in update_data.items():
        setattr(db_node, field, value)

    db_node.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_node)
    return db_node


def update_node_status(
    db: Session,
    node_id: str,
    status: NodeStatus,
    last_seen: Optional[datetime] = None,
) -> Optional[NodeModel]:
    """Update node status and last_seen timestamp."""
    db_node = get_node(db, node_id)
    if not db_node:
        return None

    db_node.status = status
    db_node.last_seen = last_seen or datetime.utcnow()
    db_node.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_node)
    return db_node


def delete_node(db: Session, node_id: str) -> bool:
    """Delete a node."""
    db_node = get_node(db, node_id)
    if not db_node:
        return False

    db.delete(db_node)
    db.commit()
    return True


# ============================================================================
# Job CRUD Operations
# ============================================================================


def create_job(db: Session, job: JobCreate) -> JobModel:
    """Create a new job."""
    db_job = JobModel(
        type=job.type,
        node_id=str(job.node_id),
        status=JobStatus.PENDING,
        payload=job.payload,
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


def get_job(db: Session, job_id: str) -> Optional[JobModel]:
    """Get a job by ID."""
    return db.query(JobModel).filter(JobModel.id == job_id).first()


def get_jobs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    node_id: Optional[str] = None,
    status: Optional[JobStatus] = None,
    job_type: Optional[JobType] = None,
) -> List[JobModel]:
    """Get all jobs with optional filtering."""
    query = db.query(JobModel)

    if node_id:
        query = query.filter(JobModel.node_id == node_id)
    if status:
        query = query.filter(JobModel.status == status)
    if job_type:
        query = query.filter(JobModel.type == job_type)

    return query.order_by(JobModel.created_at.desc()).offset(skip).limit(limit).all()


def get_jobs_count(
    db: Session,
    node_id: Optional[str] = None,
    status: Optional[JobStatus] = None,
    job_type: Optional[JobType] = None,
) -> int:
    """Get total count of jobs with optional filtering."""
    query = db.query(JobModel)

    if node_id:
        query = query.filter(JobModel.node_id == node_id)
    if status:
        query = query.filter(JobModel.status == status)
    if job_type:
        query = query.filter(JobModel.type == job_type)

    return query.count()


def update_job_status(
    db: Session,
    job_id: str,
    status: JobStatus,
    result: Optional[dict] = None,
) -> Optional[JobModel]:
    """Update job status and result."""
    db_job = get_job(db, job_id)
    if not db_job:
        return None

    db_job.status = status
    db_job.updated_at = datetime.utcnow()

    if status == JobStatus.RUNNING and not db_job.started_at:
        db_job.started_at = datetime.utcnow()

    if status in (JobStatus.COMPLETED, JobStatus.FAILED):
        db_job.completed_at = datetime.utcnow()
        if result:
            db_job.result = result

    db.commit()
    db.refresh(db_job)
    return db_job


def delete_job(db: Session, job_id: str) -> bool:
    """Delete a job."""
    db_job = get_job(db, job_id)
    if not db_job:
        return False

    db.delete(db_job)
    db.commit()
    return True


# ============================================================================
# Metric CRUD Operations
# ============================================================================


def create_metric(db: Session, metric: MetricCreate) -> MetricModel:
    """Create a new metric entry."""
    db_metric = MetricModel(
        node_id=str(metric.node_id),
        timestamp=metric.timestamp,
        cpu_percent=metric.cpu_percent,
        memory_percent=metric.memory_percent,
        disk_percent=metric.disk_percent,
        temperature=metric.temperature,
    )
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    return db_metric


def get_metrics(
    db: Session,
    node_id: str,
    skip: int = 0,
    limit: int = 100,
    since: Optional[datetime] = None,
) -> List[MetricModel]:
    """Get metrics for a node with optional time filtering."""
    query = db.query(MetricModel).filter(MetricModel.node_id == node_id)

    if since:
        query = query.filter(MetricModel.timestamp >= since)

    return query.order_by(MetricModel.timestamp.desc()).offset(skip).limit(limit).all()


def get_latest_metric(db: Session, node_id: str) -> Optional[MetricModel]:
    """Get the most recent metric for a node."""
    return (
        db.query(MetricModel)
        .filter(MetricModel.node_id == node_id)
        .order_by(MetricModel.timestamp.desc())
        .first()
    )


def get_metrics_stats(
    db: Session,
    node_id: str,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
) -> Optional[dict]:
    """
    Get aggregated statistics for metrics over a time period.

    Returns a dictionary with min, max, and avg for each metric type.
    Returns None if no metrics found in the time range.
    """
    from sqlalchemy import func

    query = db.query(
        func.count(MetricModel.id).label("count"),
        func.min(MetricModel.timestamp).label("start_time"),
        func.max(MetricModel.timestamp).label("end_time"),
        # CPU stats
        func.avg(MetricModel.cpu_percent).label("cpu_avg"),
        func.min(MetricModel.cpu_percent).label("cpu_min"),
        func.max(MetricModel.cpu_percent).label("cpu_max"),
        # Memory stats
        func.avg(MetricModel.memory_percent).label("memory_avg"),
        func.min(MetricModel.memory_percent).label("memory_min"),
        func.max(MetricModel.memory_percent).label("memory_max"),
        # Disk stats
        func.avg(MetricModel.disk_percent).label("disk_avg"),
        func.min(MetricModel.disk_percent).label("disk_min"),
        func.max(MetricModel.disk_percent).label("disk_max"),
        # Temperature stats (can be NULL)
        func.avg(MetricModel.temperature).label("temperature_avg"),
        func.min(MetricModel.temperature).label("temperature_min"),
        func.max(MetricModel.temperature).label("temperature_max"),
    ).filter(MetricModel.node_id == node_id)

    if since:
        query = query.filter(MetricModel.timestamp >= since)
    if until:
        query = query.filter(MetricModel.timestamp <= until)

    result = query.first()

    if not result or result.count == 0:
        return None

    return {
        "count": result.count,
        "start_time": result.start_time,
        "end_time": result.end_time,
        "cpu_avg": result.cpu_avg,
        "cpu_min": result.cpu_min,
        "cpu_max": result.cpu_max,
        "memory_avg": result.memory_avg,
        "memory_min": result.memory_min,
        "memory_max": result.memory_max,
        "disk_avg": result.disk_avg,
        "disk_min": result.disk_min,
        "disk_max": result.disk_max,
        "temperature_avg": result.temperature_avg,
        "temperature_min": result.temperature_min,
        "temperature_max": result.temperature_max,
    }


def delete_old_metrics(db: Session, before: datetime) -> int:
    """Delete metrics older than the specified datetime."""
    deleted = db.query(MetricModel).filter(MetricModel.timestamp < before).delete()
    db.commit()
    return deleted
