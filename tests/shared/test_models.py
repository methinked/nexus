from datetime import datetime
import pytest
from pydantic import ValidationError
from nexus.shared.models import (
    MetricData,
    Node,
    NodeStatus,
    HealthThresholds,
    Job,
    JobType,
    JobStatus
)

class TestMetricData:
    def test_valid_metrics(self):
        """Test creating a valid MetricData object."""
        m = MetricData(
            cpu_percent=50.0,
            memory_percent=60.0,
            disk_percent=70.0,
            temperature=45.5
        )
        assert m.cpu_percent == 50.0
        assert m.temperature == 45.5

    def test_invalid_percentages(self):
        """Test that percentages must be 0-100."""
        with pytest.raises(ValidationError):
            MetricData(
                cpu_percent=101.0,  # Invalid
                memory_percent=50.0,
                disk_percent=50.0
            )

    def test_invalid_temperature_low(self):
        """Test temperature lower bound."""
        with pytest.raises(ValidationError):
            MetricData(
                cpu_percent=50.0,
                memory_percent=50.0,
                disk_percent=50.0,
                temperature=-51.0  # Too cold
            )

    def test_invalid_temperature_high(self):
        """Test temperature upper bound."""
        with pytest.raises(ValidationError):
            MetricData(
                cpu_percent=50.0,
                memory_percent=50.0,
                disk_percent=50.0,
                temperature=151.0  # Too hot
            )

class TestNodeModels:
    def test_node_defaults(self):
        """Test Node model default values."""
        node = Node(
            name="test-node",
            ip_address="192.168.1.100",
            shared_secret="secret123"
        )
        assert node.status == NodeStatus.OFFLINE
        assert node.id is not None
        assert node.created_at is not None

class TestHealthThresholds:
    def test_default_thresholds(self):
        """Test that defaults match the spec."""
        t = HealthThresholds()
        assert t.cpu_warning == 80.0
        assert t.cpu_critical == 95.0

class TestJobModels:
    def test_job_enums(self):
        """Test JobType and JobStatus enum values."""
        job = Job(
            type=JobType.SHELL,
            node_id="123e4567-e89b-12d3-a456-426614174000",
            payload={"command": "echo hello"}
        )
        assert job.status == JobStatus.PENDING
        assert job.type == "shell"
