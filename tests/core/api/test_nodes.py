from datetime import datetime
from uuid import uuid4
from nexus.core.db.models import NodeModel
from nexus.shared.models import NodeMetadata, NodeStatus

def create_test_node(db, name="test-node"):
    """Helper to create a node in the DB."""
    node = NodeModel(
        id=str(uuid4()),
        name=name,
        ip_address="192.168.1.100",
        status=NodeStatus.ONLINE,
        node_metadata={"location": "Test Lab", "tags": ["test"]},
        last_seen=datetime.utcnow()
    )
    db.add(node)
    db.commit()
    return node

def test_list_nodes_empty(client):
    """Test listing nodes when DB is empty."""
    response = client.get("/api/nodes")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["nodes"] == []

def test_list_nodes_populated(client, db_session):
    """Test listing nodes with data."""
    create_test_node(db_session, "node-1")
    create_test_node(db_session, "node-2")
    
    response = client.get("/api/nodes")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["nodes"]) == 2
    assert data["nodes"][0]["name"] == "node-1"

def test_get_node_details(client, db_session):
    """Test retrieving specific node details."""
    node = create_test_node(db_session)
    response = client.get(f"/api/nodes/{node.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(node.id)
    assert data["name"] == "test-node"
    assert data["metadata"]["location"] == "Test Lab"

def test_get_node_not_found(client):
    """Test 404 for non-existent node."""
    fake_id = str(uuid4())
    response = client.get(f"/api/nodes/{fake_id}")
    assert response.status_code == 404

def test_update_node_metadata(client, db_session):
    """Test updating node metadata."""
    node = create_test_node(db_session)
    payload = {
        "metadata": {
            "location": "New Location",
            "tags": ["updated"]
        }
    }
    response = client.put(f"/api/nodes/{node.id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["location"] == "New Location"
    assert "updated" in data["metadata"]["tags"]
