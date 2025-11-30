"""
Health calculation service for Nexus Core.

Calculates node health status based on system metrics and configurable thresholds.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from nexus.shared import (
    HealthThresholds,
    Metric,
    NodeHealth,
    NodeHealthStatus,
)


def calculate_component_health(
    value: float,
    warning_threshold: float,
    critical_threshold: float,
) -> NodeHealth:
    """
    Calculate health status for a single metric component.

    Args:
        value: Current metric value (percentage)
        warning_threshold: Warning level threshold
        critical_threshold: Critical level threshold

    Returns:
        NodeHealth status (HEALTHY, WARNING, or CRITICAL)
    """
    if value >= critical_threshold:
        return NodeHealth.CRITICAL
    elif value >= warning_threshold:
        return NodeHealth.WARNING
    else:
        return NodeHealth.HEALTHY


def calculate_node_health(
    node_id: UUID,
    latest_metric: Optional[Metric],
    thresholds: Optional[HealthThresholds] = None,
) -> NodeHealthStatus:
    """
    Calculate overall health status for a node based on latest metrics.

    Args:
        node_id: Node UUID
        latest_metric: Most recent metric data (None if no metrics exist)
        thresholds: Custom thresholds (uses defaults if not provided)

    Returns:
        NodeHealthStatus with detailed breakdown
    """
    if thresholds is None:
        thresholds = HealthThresholds()

    # If no metrics, health is unknown
    if latest_metric is None:
        return NodeHealthStatus(
            node_id=node_id,
            overall_health=NodeHealth.UNKNOWN,
            last_check=datetime.utcnow(),
            cpu_health=NodeHealth.UNKNOWN,
            memory_health=NodeHealth.UNKNOWN,
            disk_health=NodeHealth.UNKNOWN,
            temperature_health=NodeHealth.UNKNOWN,
            latest_metrics=None,
            thresholds=thresholds,
        )

    # Calculate component health
    cpu_health = calculate_component_health(
        latest_metric.cpu_percent,
        thresholds.cpu_warning,
        thresholds.cpu_critical,
    )

    memory_health = calculate_component_health(
        latest_metric.memory_percent,
        thresholds.memory_warning,
        thresholds.memory_critical,
    )

    disk_health = calculate_component_health(
        latest_metric.disk_percent,
        thresholds.disk_warning,
        thresholds.disk_critical,
    )

    # Temperature health (optional, only if available and thresholds set)
    temperature_health = None
    if latest_metric.temperature is not None:
        if thresholds.temperature_warning and thresholds.temperature_critical:
            temperature_health = calculate_component_health(
                latest_metric.temperature,
                thresholds.temperature_warning,
                thresholds.temperature_critical,
            )

    # Overall health is worst of all components
    all_healths = [cpu_health, memory_health, disk_health]
    if temperature_health is not None:
        all_healths.append(temperature_health)

    # Priority: CRITICAL > WARNING > HEALTHY
    if NodeHealth.CRITICAL in all_healths:
        overall_health = NodeHealth.CRITICAL
    elif NodeHealth.WARNING in all_healths:
        overall_health = NodeHealth.WARNING
    else:
        overall_health = NodeHealth.HEALTHY

    return NodeHealthStatus(
        node_id=node_id,
        overall_health=overall_health,
        last_check=datetime.utcnow(),
        cpu_health=cpu_health,
        memory_health=memory_health,
        disk_health=disk_health,
        temperature_health=temperature_health,
        latest_metrics=latest_metric,
        thresholds=thresholds,
    )
