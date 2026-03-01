from nexus.core.db.models import NodeModel

def test_register_new_node(client, db_session):
    """Test registering a fresh node."""
    payload = {
        "name": "new-node",
        "ip_address": "192.168.1.50",
        "port": 8000,
        "shared_secret": "change-me-in-production",
        "platform_system": "Linux",
        "platform_release": "5.10.0",
        "machine": "x86_64",
        "processor": "Intel",
        "total_memory": 8589934592,
        "location": "Server Room"
    }
    
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    
    assert "node_id" in data
    assert "api_token" in data
    # assert data["token_type"] == "bearer" # Not in RegistrationResponse model
    
    # Verify DB
    node = db_session.query(NodeModel).filter_by(name="new-node").first()
    assert node is not None
    assert node.status == "online"

def test_register_duplicate_node_name(client, db_session, test_node):
    """Test registering a node with an existing name (should update or fail depending on logic)."""
    # Assuming registration is idempotent-ish or allows re-registration
    payload = {
        "name": test_node.name,
        "ip_address": "192.168.1.101", # IP changed
        "port": 8000,
        "shared_secret": "change-me-in-production"
    }
    
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    
    assert data["node_id"] == test_node.id  # Should reuse ID
    
    # Verify DB update
    db_session.refresh(test_node)
    assert test_node.ip_address == "192.168.1.101"

def test_register_invalid_payload(client):
    """Test registration with missing required fields."""
    payload = {"name": "bad-node"} # Missing IP, etc
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422
