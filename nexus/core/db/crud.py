"""
CRUD operations for database models.

Provides create, read, update, and delete operations for nodes, jobs, metrics,
services, and deployments (Phase 7 - Docker Orchestration).
"""

import uuid
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from nexus.core.db.models import DeploymentModel, JobModel, MetricModel, NodeModel, ServiceModel
from nexus.shared.models import (
    DeploymentCreate,
    DeploymentStatus,
    DeploymentUpdate,
    JobCreate,
    JobStatus,
    JobType,
    MetricCreate,
    NodeCreate,
    NodeStatus,
    ServiceCreate,
    ServiceUpdate,
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


# ============================================================================
# Log CRUD Operations
# ============================================================================


def create_log(db: Session, log: "LogCreate") -> "LogModel":
    """Create a new log entry."""
    from nexus.core.db.models import LogModel

    db_log = LogModel(
        node_id=str(log.node_id),
        timestamp=log.timestamp,
        level=log.level.value,
        source=log.source,
        message=log.message,
        extra=log.extra,
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def get_logs(
    db: Session,
    node_id: Optional[str] = None,
    level: Optional[str] = None,
    source: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
) -> List["LogModel"]:
    """Get logs with optional filtering."""
    from nexus.core.db.models import LogModel

    query = db.query(LogModel)

    if node_id:
        query = query.filter(LogModel.node_id == node_id)
    if level:
        query = query.filter(LogModel.level == level)
    if source:
        query = query.filter(LogModel.source.like(f"%{source}%"))
    if since:
        query = query.filter(LogModel.timestamp >= since)
    if until:
        query = query.filter(LogModel.timestamp <= until)

    return query.order_by(LogModel.timestamp.desc()).offset(skip).limit(limit).all()


def get_logs_count(
    db: Session,
    node_id: Optional[str] = None,
    level: Optional[str] = None,
    source: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
) -> int:
    """Get count of logs matching filters."""
    from nexus.core.db.models import LogModel

    query = db.query(LogModel)

    if node_id:
        query = query.filter(LogModel.node_id == node_id)
    if level:
        query = query.filter(LogModel.level == level)
    if source:
        query = query.filter(LogModel.source.like(f"%{source}%"))
    if since:
        query = query.filter(LogModel.timestamp >= since)
    if until:
        query = query.filter(LogModel.timestamp <= until)

    return query.count()


def delete_old_logs(db: Session, before: datetime) -> int:
    """Delete logs older than the specified datetime."""
    from nexus.core.db.models import LogModel

    deleted = db.query(LogModel).filter(LogModel.timestamp < before).delete()
    db.commit()
    return deleted


# ============================================================================
# Service CRUD Operations (Phase 7 - Docker Orchestration)
# ============================================================================


def create_service(db: Session, service: ServiceCreate) -> ServiceModel:
    """Create a new service template."""
    from nexus.core.db.models import ServiceModel

    db_service = ServiceModel(
        id=str(uuid.uuid4()),
        name=service.name,
        display_name=service.display_name,
        description=service.description,
        version=service.version,
        category=service.category,
        docker_compose=service.docker_compose,
        default_env=service.default_env,
        icon_url=service.icon_url,
    )
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service


def get_service(db: Session, service_id: str) -> Optional[ServiceModel]:
    """Get a service by ID."""
    from nexus.core.db.models import ServiceModel

    return db.query(ServiceModel).filter(ServiceModel.id == service_id).first()


def get_service_by_name(db: Session, name: str) -> Optional[ServiceModel]:
    """Get a service by name."""
    from nexus.core.db.models import ServiceModel

    return db.query(ServiceModel).filter(ServiceModel.name == name).first()


def get_services(
    db: Session, skip: int = 0, limit: int = 100, category: Optional[str] = None
) -> list[ServiceModel]:
    """Get list of services with optional filtering."""
    from nexus.core.db.models import ServiceModel

    query = db.query(ServiceModel)

    if category:
        query = query.filter(ServiceModel.category == category)

    return query.offset(skip).limit(limit).all()


def get_services_count(db: Session, category: Optional[str] = None) -> int:
    """Get count of services matching filters."""
    from nexus.core.db.models import ServiceModel

    query = db.query(ServiceModel)

    if category:
        query = query.filter(ServiceModel.category == category)

    return query.count()


def update_service(db: Session, service_id: str, service_update: ServiceUpdate) -> Optional[ServiceModel]:
    """Update a service template."""
    from nexus.core.db.models import ServiceModel

    db_service = db.query(ServiceModel).filter(ServiceModel.id == service_id).first()
    if not db_service:
        return None

    update_data = service_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_service, field, value)

    db_service.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_service)
    return db_service


def delete_service(db: Session, service_id: str) -> bool:
    """Delete a service template."""
    from nexus.core.db.models import ServiceModel

    db_service = db.query(ServiceModel).filter(ServiceModel.id == service_id).first()
    if not db_service:
        return False

    db.delete(db_service)
    db.commit()
    return True


# ============================================================================
# Deployment CRUD Operations (Phase 7 - Docker Orchestration)
# ============================================================================


def create_deployment(db: Session, deployment: DeploymentCreate) -> DeploymentModel:
    """Create a new deployment."""
    from nexus.core.db.models import DeploymentModel

    # Convert DeploymentConfig to dict
    config_dict = deployment.config.model_dump() if deployment.config else {}

    db_deployment = DeploymentModel(
        id=str(uuid.uuid4()),
        name=deployment.name,
        service_id=str(deployment.service_id),
        node_id=str(deployment.node_id),
        config=config_dict,
        status=DeploymentStatus.DEPLOYING,
    )
    db.add(db_deployment)
    db.commit()
    db.refresh(db_deployment)
    return db_deployment


def get_deployment(db: Session, deployment_id: str) -> Optional[DeploymentModel]:
    """Get a deployment by ID."""
    from nexus.core.db.models import DeploymentModel

    return db.query(DeploymentModel).filter(DeploymentModel.id == deployment_id).first()


def get_deployments(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    node_id: Optional[str] = None,
    service_id: Optional[str] = None,
    status: Optional[DeploymentStatus] = None,
) -> list[DeploymentModel]:
    """Get list of deployments with optional filtering."""
    from nexus.core.db.models import DeploymentModel

    query = db.query(DeploymentModel)

    if node_id:
        query = query.filter(DeploymentModel.node_id == node_id)
    if service_id:
        query = query.filter(DeploymentModel.service_id == service_id)
    if status:
        query = query.filter(DeploymentModel.status == status)

    return query.order_by(DeploymentModel.created_at.desc()).offset(skip).limit(limit).all()


def get_deployments_count(
    db: Session,
    node_id: Optional[str] = None,
    service_id: Optional[str] = None,
    status: Optional[DeploymentStatus] = None,
) -> int:
    """Get count of deployments matching filters."""
    from nexus.core.db.models import DeploymentModel

    query = db.query(DeploymentModel)

    if node_id:
        query = query.filter(DeploymentModel.node_id == node_id)
    if service_id:
        query = query.filter(DeploymentModel.service_id == service_id)
    if status:
        query = query.filter(DeploymentModel.status == status)

    return query.count()


def update_deployment(
    db: Session, deployment_id: str, deployment_update: DeploymentUpdate
) -> Optional[DeploymentModel]:
    """Update a deployment."""
    from nexus.core.db.models import DeploymentModel

    db_deployment = db.query(DeploymentModel).filter(DeploymentModel.id == deployment_id).first()
    if not db_deployment:
        return None

    update_data = deployment_update.model_dump(exclude_unset=True)

    # Handle DeploymentConfig separately
    if "config" in update_data and update_data["config"]:
        update_data["config"] = update_data["config"].model_dump()

    for field, value in update_data.items():
        setattr(db_deployment, field, value)

    db_deployment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_deployment)
    return db_deployment


def update_deployment_status(
    db: Session, deployment_id: str, status: DeploymentStatus, container_id: Optional[str] = None
) -> Optional[DeploymentModel]:
    """Update deployment status and optionally container ID."""
    from nexus.core.db.models import DeploymentModel

    db_deployment = db.query(DeploymentModel).filter(DeploymentModel.id == deployment_id).first()
    if not db_deployment:
        return None

    db_deployment.status = status
    if container_id:
        db_deployment.container_id = container_id

    # Set deployed_at timestamp when first deployed
    if status == DeploymentStatus.RUNNING and not db_deployment.deployed_at:
        db_deployment.deployed_at = datetime.utcnow()

    db_deployment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_deployment)
    return db_deployment


def delete_deployment(db: Session, deployment_id: str) -> bool:
    """Delete a deployment."""
    from nexus.core.db.models import DeploymentModel

    db_deployment = db.query(DeploymentModel).filter(DeploymentModel.id == deployment_id).first()
    if not db_deployment:
        return False

    db.delete(db_deployment)
    db.commit()
    return True
