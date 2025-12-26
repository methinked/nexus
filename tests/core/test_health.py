import pytest
from uuid import uuid4
from datetime import datetime
from nexus.core.services.health import calculate_component_health, calculate_node_health
from nexus.shared.models import NodeHealth, NodeHealthStatus, Metric, HealthThresholds

class TestComponentHealth:
    def test_healthy(self):
        """Value below warning threshold should be HEALTHY."""
        status = calculate_component_health(50.0, 80.0, 90.0)
        assert status == NodeHealth.HEALTHY

    def test_warning(self):
        """Value between warning and critical should be WARNING."""
        status = calculate_component_health(85.0, 80.0, 90.0)
        assert status == NodeHealth.WARNING

    def test_critical(self):
        """Value above critical should be CRITICAL."""
        status = calculate_component_health(95.0, 80.0, 90.0)
        assert status == NodeHealth.CRITICAL

    def test_exact_boundary(self):
        """Value exactly at threshold should trigger the alert."""
        assert calculate_component_health(80.0, 80.0, 90.0) == NodeHealth.WARNING
        assert calculate_component_health(90.0, 80.0, 90.0) == NodeHealth.CRITICAL

class TestNodeHealthCalculation:
    @pytest.fixture
    def node_id(self):
        return uuid4()

    @pytest.fixture
    def base_metric(self, node_id):
        return Metric(
            node_id=node_id,
            timestamp=datetime.utcnow(),
            cpu_percent=10.0,
            memory_percent=20.0,
            disk_percent=30.0,
            temperature=40.0
        )

    def test_metric_none_returns_unknown(self, node_id):
        """If no metrics exist, status should be UNKNOWN."""
        status = calculate_node_health(node_id, None)
        assert status.overall_health == NodeHealth.UNKNOWN
        assert status.cpu_health == NodeHealth.UNKNOWN

    def test_healthy_metrics(self, node_id, base_metric):
        """All metrics low should return HEALTHY."""
        status = calculate_node_health(node_id, base_metric)
        assert status.overall_health == NodeHealth.HEALTHY

    def test_single_critical_component(self, node_id, base_metric):
        """One critical component makes the whole node CRITICAL."""
        base_metric.cpu_percent = 99.0  # Critical
        status = calculate_node_health(node_id, base_metric)
        assert status.cpu_health == NodeHealth.CRITICAL
        assert status.overall_health == NodeHealth.CRITICAL

    def test_single_warning_component(self, node_id, base_metric):
        """One warning component makes the whole node WARNING."""
        base_metric.memory_percent = 88.0  # Warning (default is 85)
        status = calculate_node_health(node_id, base_metric)
        assert status.memory_health == NodeHealth.WARNING
        assert status.overall_health == NodeHealth.WARNING

    def test_custom_thresholds(self, node_id, base_metric):
        """Should respect custom thresholds passed in."""
        # Standard warning is 80, but we set it to 5
        custom_thresholds = HealthThresholds(cpu_warning=5.0, cpu_critical=90.0)
        base_metric.cpu_percent = 10.0  # This is > 5.0, so should be WARNING
        
        status = calculate_node_health(node_id, base_metric, thresholds=custom_thresholds)
        assert status.cpu_health == NodeHealth.WARNING
        assert status.overall_health == NodeHealth.WARNING
