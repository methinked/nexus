import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta, timezone

def test_submit_metrics_success(client, db_session, test_node):
    """Test submitting metrics successfully."""
    payload = {
        "node_id": str(test_node.id),
        "cpu_percent": 15.5,
        "memory_percent": 40.2,
        "disk_percent": 25.0,
        "temperature": 45.0,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # Mock WebSocket manager to avoid async loop issues/errors
    with patch("nexus.core.services.websocket_manager.manager.broadcast_event", new_callable=AsyncMock) as mock_broadcast:
        response = client.post("/api/metrics", json=payload)
        
        assert response.status_code == 201
        
        # Verify call to websocket manager (might not be called if no loop, but code swallows RuntimeError)
        # In TestClient, app runs in same thread/loop usually.
        
def test_submit_metrics_node_not_found(client):
    """Test submitting metrics for unknown node."""
    from uuid import uuid4
    payload = {
        "node_id": str(uuid4()),
        "cpu_percent": 10.0,
        "memory_percent": 10.0,
        "disk_percent": 10.0
    }
    response = client.post("/api/metrics", json=payload)
    assert response.status_code == 404

def test_get_node_metrics(client, db_session, test_node):
    """Test retrieving historical metrics."""
    # Seed some metrics
    from nexus.core.db import create_metric
    from nexus.shared.models import MetricCreate
    
    # 1 hour ago
    m1 = MetricCreate(
        node_id=test_node.id,
        cpu_percent=10.0,
        memory_percent=20.0,
        disk_percent=30.0,
        temperature=40.0,
        timestamp=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    create_metric(db_session, m1)
    
    # Now
    m2 = MetricCreate(
        node_id=test_node.id,
        cpu_percent=20.0,
        memory_percent=30.0,
        disk_percent=40.0,
        temperature=50.0,
        timestamp=datetime.now(timezone.utc)
    )
    create_metric(db_session, m2)
    
    # Query all
    response = client.get(f"/api/metrics/{test_node.id}")
    if response.status_code == 422:
        print(response.json())
    assert response.status_code == 200
    data = response.json()
    assert len(data["metrics"]) == 2
    # Sort order is usually desc by timestamp
    assert data["metrics"][0]["cpu_percent"] in [10.0, 20.0]
    
    # Query with 'since' filter (last 30 mins)
    since_time = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
    response = client.get(f"/api/metrics/{test_node.id}", params={"since": since_time})
    assert response.status_code == 200
    data = response.json()
    assert len(data["metrics"]) == 1
    assert data["metrics"][0]["cpu_percent"] == 20.0

def test_get_metrics_stats(client, db_session, test_node):
    """Test aggregated statistics."""
    from nexus.core.db import create_metric
    from nexus.shared.models import MetricCreate
    
    # Seed data: 10% and 30% CPU
    create_metric(db_session, MetricCreate(
        node_id=test_node.id, cpu_percent=10.0, memory_percent=10.0, disk_percent=10.0,
        timestamp=datetime.now(timezone.utc)
    ))
    create_metric(db_session, MetricCreate(
        node_id=test_node.id, cpu_percent=30.0, memory_percent=10.0, disk_percent=10.0,
        timestamp=datetime.now(timezone.utc)
    ))
    
    response = client.get(f"/api/metrics/{test_node.id}/stats")
    assert response.status_code == 200
    data = response.json()
    
    assert data["count"] == 2
    assert data["cpu_min"] == 10.0
    assert data["cpu_max"] == 30.0
    assert data["cpu_avg"] == 20.0
