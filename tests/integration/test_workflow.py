import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from nexus.core.main import app as core_app
from nexus.agent.main import app as agent_app
from nexus.shared.models import JobType, JobStatus
from uuid import uuid4

@pytest.fixture
def core_client(db_session, mock_config):
    """Core API Client with DB override."""
    # Note: re-using the logic from conftest.py if possible, but defining here for clarity
    from nexus.core.db.database import get_db
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    core_app.dependency_overrides[get_db] = override_get_db
    with TestClient(core_app) as c:
        yield c
    core_app.dependency_overrides.clear()

@pytest.fixture
def agent_client():
    """Agent API Client."""
    with TestClient(agent_app) as c:
        yield c

@pytest.mark.asyncio
async def test_agent_registration_flow(core_client, agent_client, db_session):
    """
    Test the full registration flow:
    1. Agent starts up (simulated)
    2. Agent calls Core /register
    3. Core saves node
    4. Agent gets token
    """
    # We need to simulate the Agent's register_with_core function calling the Core API
    # Since agent code uses httpx.AsyncClient, we mock that to call our core_client
    
    # But wait, httpx and TestClient are slightly different. 
    # Simplest way: Mock the response of httpx in Agent to return what Core returns
    
    from nexus.shared.models import RegistrationResponse
    
    # 1. Simulate Agent calling Register
    # We will verify Core's behavior first via Client
    payload = {
        "name": "integration-agent",
        "ip_address": "127.0.0.1",
        "shared_secret": "change-me-in-production",
        "metadata": {"description": "Integration Test Agent"}
    }
    
    response = core_client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    
    node_id = data["node_id"]
    api_token = data["api_token"]
    
    assert node_id is not None
    assert api_token is not None
    
    # 2. Verify Node exists in DB
    from nexus.core.db.models import NodeModel
    node = db_session.query(NodeModel).filter_by(id=str(node_id)).first()
    assert node is not None
    assert node.name == "integration-agent"

@pytest.mark.asyncio
async def test_job_execution_flow(core_client, agent_client, db_session):
    """
    Test Job submission flow:
    1. Submit Job to Core
    2. Core invokes Agent /execute (Mocked)
    3. Agent executes and returns status
    4. Core updates DB
    """
    # Setup: Create a registered node
    from nexus.core.db import create_node
    from nexus.shared.models import NodeCreate
    
    node_data = NodeCreate(
        name="job-runner",
        ip_address="127.0.0.1",
        shared_secret="change-me-in-production"
    )
    node = create_node(db_session, node_data)
    
    # Test Job Payload
    job_payload = {
        "type": JobType.SHELL,
        "node_id": str(node.id),
        "payload": {"command": "echo 'integration test'"}
    }
    
    # We need to patch the Core's call to the Agent
    # Core uses httpx.AsyncClient().post(agent_url, ...)
    # We need this to NOT fail, but we don't necessarily need to route it to agent_client 
    # unless we want to test Agent's internal logic too.
    # Let's mock a successful 200 OK from "Agent"
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_agent_call:
        mock_agent_call.return_value.status_code = 200
        
        # 1. Submit to Core
        response = core_client.post("/api/jobs", json=job_payload)
        assert response.status_code == 201
        job_data = response.json()
        job_id = job_data["id"]
        
        assert job_data["status"] == "pending"
        
        # Verify Core tried to call Agent
        mock_agent_call.assert_called_once()
        expected_url = f"http://127.0.0.1:8001/api/jobs/{job_id}/execute"
        
        # httpx.post(url, json=...) -> args=(url,), kwargs={'json': ...}
        args, kwargs = mock_agent_call.call_args
        assert args[0] == expected_url
        assert kwargs["json"]["type"] == "shell"

    # 2. Simulate Agent callback (Update Status)
    # The actual Agent would execute code and call PATCH /api/jobs/{id}
    callback_payload = {
        "status": "completed",
        "result": {"output": "integration test\n", "exit_code": 0}
    }
    
    response = core_client.patch(f"/api/jobs/{job_id}", json=callback_payload)
    assert response.status_code == 200
    
    # 3. Verify Final State in DB
    response = core_client.get(f"/api/jobs/{job_id}")
    assert response.json()["status"] == "completed"
    assert response.json()["result"]["output"] == "integration test\n"

