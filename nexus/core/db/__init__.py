"""
Database layer for Nexus Core.

Provides SQLAlchemy models, CRUD operations, and database session management.
"""

from nexus.core.db.crud import (
    create_job,
    create_metric,
    create_node,
    delete_job,
    delete_node,
    delete_old_metrics,
    get_job,
    get_jobs,
    get_jobs_count,
    get_latest_metric,
    get_metrics,
    get_metrics_stats,
    get_node,
    get_node_by_name,
    get_nodes,
    get_nodes_count,
    update_job_status,
    update_node,
    update_node_status,
)
from nexus.core.db.database import Base, SessionLocal, engine, get_db, init_db
from nexus.core.db.models import JobModel, MetricModel, NodeModel

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
]
