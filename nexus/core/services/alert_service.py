"""
Alert service for Nexus Core.

Periodically checks node status and metrics to generate alerts.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from nexus.core.db import (
    create_alert,
    get_nodes,
    get_latest_metric,
    resolve_alerts_by_type,
)
from nexus.core.db.database import SessionLocal
from nexus.shared.config import CoreConfig
from nexus.shared.models import (
    AlertCreate,
    AlertSeverity,
    AlertType,
    NodeStatus,
)

logger = logging.getLogger(__name__)


class AlertService:
    """
    Background service that monitors system health and manages alerts.
    """

    def __init__(self, config: CoreConfig):
        self.config = config
        self.task: Optional[asyncio.Task] = None
        self.running = False
        self.check_interval_seconds = 60  # Check every minute

        # Thresholds (Could be configurable per node later)
        self.thresholds = {
            "patience_offline_seconds": 120, # 2 minutes before declaring offline
            "cpu_warning": 80.0,
            "cpu_critical": 90.0,
            "memory_warning": 85.0,
            "memory_critical": 95.0,
            "disk_warning": 85.0,
            "disk_critical": 95.0,
            "temp_critical": 80.0,
        }

    async def start(self):
        """Start the alert service."""
        logger.info(f"Starting alert service (interval={self.check_interval_seconds}s)")
        self.running = True
        self.task = asyncio.create_task(self._monitor_loop())

    async def stop(self):
        """Stop the alert service."""
        if self.task:
            self.running = False
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Alert service stopped")

    async def _monitor_loop(self):
        """Main monitoring loop."""
        # Initial delay
        await asyncio.sleep(10)

        while self.running:
            try:
                await self._check_all_nodes()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert monitor loop: {e}", exc_info=True)
                # Prevent tight loop on error
                await asyncio.sleep(5)
            
            await asyncio.sleep(self.check_interval_seconds)

    async def _check_all_nodes(self):
        """Check health of all registered nodes."""
        db: Session = SessionLocal()
        try:
            nodes = get_nodes(db)
            for node in nodes:
                await self._check_node(db, node)
        finally:
            db.close()

    async def _check_node(self, db: Session, node):
        """Check a single node for alert conditions."""
        
        # 1. Check Offline Status
        await self._check_node_offline(db, node)

        # 2. Check Resource Usage (only if online)
        if node.status == NodeStatus.ONLINE:
            latest_metric = get_latest_metric(db, str(node.id))
            if latest_metric:
                await self._check_resources(db, node, latest_metric)

    async def _check_node_offline(self, db: Session, node):
        """Check if node is offline."""
        if not node.last_seen:
            return

        time_since_seen = (datetime.utcnow() - node.last_seen).total_seconds()
        
        if time_since_seen > self.thresholds["patience_offline_seconds"]:
            # Node is offline - Trigger Alert
            self._trigger_alert(
                db, 
                node.id, 
                AlertType.NODE_OFFLINE, 
                AlertSeverity.CRITICAL,
                f"Node {node.name} is offline (last seen {int(time_since_seen)}s ago)"
            )
            # Update node status to OFFLINE to satisfy UI
            from nexus.core.db.crud import update_node_status
            update_node_status(db, str(node.id), NodeStatus.OFFLINE, node.last_seen)
        else:
            # Node is online - Resolve Alert
            resolve_alerts_by_type(db, str(node.id), AlertType.NODE_OFFLINE)

    async def _check_resources(self, db: Session, node, metric):
        """Check resource metrics."""
        
        # CPU
        if metric.cpu_percent > self.thresholds["cpu_critical"]:
            self._trigger_alert(db, node.id, AlertType.HIGH_CPU, AlertSeverity.CRITICAL, f"High CPU usage: {metric.cpu_percent:.1f}%")
        elif metric.cpu_percent > self.thresholds["cpu_warning"]:
            self._trigger_alert(db, node.id, AlertType.HIGH_CPU, AlertSeverity.WARNING, f"Elevated CPU usage: {metric.cpu_percent:.1f}%")
        else:
            resolve_alerts_by_type(db, str(node.id), AlertType.HIGH_CPU)

        # Memory
        if metric.memory_percent > self.thresholds["memory_critical"]:
            self._trigger_alert(db, node.id, AlertType.HIGH_MEMORY, AlertSeverity.CRITICAL, f"High Memory usage: {metric.memory_percent:.1f}%")
        elif metric.memory_percent > self.thresholds["memory_warning"]:
            self._trigger_alert(db, node.id, AlertType.HIGH_MEMORY, AlertSeverity.WARNING, f"Elevated Memory usage: {metric.memory_percent:.1f}%")
        else:
            resolve_alerts_by_type(db, str(node.id), AlertType.HIGH_MEMORY)

        # Disk
        if metric.disk_percent > self.thresholds["disk_critical"]:
            self._trigger_alert(db, node.id, AlertType.HIGH_DISK, AlertSeverity.CRITICAL, f"Critical Disk usage: {metric.disk_percent:.1f}%")
        elif metric.disk_percent > self.thresholds["disk_warning"]:
            self._trigger_alert(db, node.id, AlertType.HIGH_DISK, AlertSeverity.WARNING, f"High Disk usage: {metric.disk_percent:.1f}%")
        else:
            resolve_alerts_by_type(db, str(node.id), AlertType.HIGH_DISK)

        # Temperature
        if metric.temperature and metric.temperature > self.thresholds["temp_critical"]:
             self._trigger_alert(db, node.id, AlertType.HIGH_TEMP, AlertSeverity.CRITICAL, f"High Temperature: {metric.temperature:.1f}°C")
        else:
            resolve_alerts_by_type(db, str(node.id), AlertType.HIGH_TEMP)


    def _trigger_alert(self, db: Session, node_id: str, type: AlertType, severity: AlertSeverity, message: str):
        """Create an alert if one doesn't already exist."""
        from nexus.core.db.models import AlertModel
        
        # Check if active alert of this type already exists
        existing = db.query(AlertModel).filter(
            AlertModel.node_id == str(node_id),
            AlertModel.type == type,
            AlertModel.status == "active"
        ).first()

        if existing:
            # Update existing alert if severity changed or just update timestamp
            if existing.severity != severity:
                existing.severity = severity
                existing.message = message
                existing.updated_at = datetime.utcnow()
                db.commit()
            return

        # Create new alert
        create_alert(db, AlertCreate(
            node_id=UUID(str(node_id)),
            type=type,
            severity=severity,
            message=message
        ))
