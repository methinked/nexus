"""
Nexus Core API routers.
"""

from nexus.core.api import (
    alerts,
    auth,
    jobs,
    logs,
    metrics,
    nodes,
    terminal,
    update,
    users,
    websocket,
)

__all__ = ["auth", "jobs", "logs", "metrics", "nodes", "terminal", "update", "websocket"]
