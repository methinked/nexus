"""
Database layer for Nexus Core.

Provides SQLAlchemy models, CRUD operations, and database session management.
"""

from nexus.core.db.crud import (
    create_deployment,
    create_job,
    create_log,
    create_metric,
    create_node,
    create_service,
    delete_deployment,
    delete_job,
    delete_node,
    delete_old_logs,
    delete_old_metrics,
    delete_service,
    get_deployment,
    get_deployments,
    get_deployments_count,
    get_job,
    get_jobs,
    get_jobs_count,
    get_latest_metric,
    get_logs,
    get_logs_count,
    get_metrics,
    get_metrics_stats,
    get_node,
    get_node_by_name,
    get_nodes,
    get_nodes_count,
    get_service,
    get_service_by_name,
    get_services,
    get_services_count,
    update_deployment,
    update_deployment_status,
    update_job_status,
    update_node,
    update_node_status,
    update_service,
)
from nexus.core.db.database import Base, SessionLocal, engine, get_db, init_db
from nexus.core.db.models import DeploymentModel, JobModel, MetricModel, NodeModel, ServiceModel

__all__ = [
    # Database
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    # Models
    "NodeModel",
    "JobModel",
    "MetricModel",
    "ServiceModel",
    "DeploymentModel",
    # CRUD - Nodes
    "create_node",
    "get_node",
    "get_node_by_name",
    "get_nodes",
    "get_nodes_count",
    "update_node",
    "update_node_status",
    "delete_node",
    # CRUD - Jobs
    "create_job",
    "get_job",
    "get_jobs",
    "get_jobs_count",
    "update_job_status",
    "delete_job",
    # CRUD - Metrics
    "create_metric",
    "get_metrics",
    "get_metrics_stats",
    "get_latest_metric",
    "delete_old_metrics",
    # CRUD - Logs
    "create_log",
    "get_logs",
    "get_logs_count",
    "delete_old_logs",
    # CRUD - Services (Phase 7)
    "create_service",
    "get_service",
    "get_service_by_name",
    "get_services",
    "get_services_count",
    "update_service",
    "delete_service",
    # CRUD - Deployments (Phase 7)
    "create_deployment",
    "get_deployment",
    "get_deployments",
    "get_deployments_count",
    "update_deployment",
    "update_deployment_status",
    "delete_deployment",
]
