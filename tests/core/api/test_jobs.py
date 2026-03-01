from unittest.mock import patch, AsyncMock
from uuid import uuid4
from nexus.shared.models import JobType, JobStatus

def test_submit_job_success(client, db_session, test_node):
    """Test submitting a job successfully."""
    payload = {
        "type": JobType.SHELL,
        "node_id": str(test_node.id),
        "payload": {
            "command": "echo hello"
        }
    }

    # Mock the external Agent call
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        
        response = client.post("/api/jobs", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        assert data["node_id"] == str(test_node.id)
        
        # Verify call to agent
        mock_post.assert_called_once()
        assert f"http://{test_node.ip_address}:8001/api/jobs" in mock_post.call_args[0][0]

def test_submit_job_agent_failure(client, db_session, test_node):
    """Test job submission when agent is unreachable."""
    payload = {
        "type": JobType.SHELL,
        "node_id": str(test_node.id),
        "payload": {"command": "echo hello"}
    }

    # Mock agent failure
    import httpx
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("Connection refused", request=None)
        
        response = client.post("/api/jobs", json=payload)
        
        assert response.status_code == 503
        data = response.json()
        assert "Agent unavailable" in data["detail"]

def test_list_jobs(client, db_session, test_node):
    """Test listing jobs."""
    # Create a job first (bypassing API to avoid mock complexity)
    from nexus.core.db import create_job
    from nexus.shared.models import JobCreate
    
    job_data = JobCreate(
        type=JobType.SHELL,
        node_id=test_node.id,
        payload={"command": "ls"}
    )
    create_job(db_session, job_data)
    
    response = client.get("/api/jobs")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["jobs"][0]["type"] == "shell"

def test_get_job_details(client, db_session, test_node):
    """Test getting specific job details."""
    from nexus.core.db import create_job
    from nexus.shared.models import JobCreate
    
    job_data = JobCreate(
        type=JobType.SHELL,
        node_id=test_node.id,
        payload={"command": "ls"}
    )
    job = create_job(db_session, job_data)
    
    response = client.get(f"/api/jobs/{job.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(job.id)

def test_update_job_status(client, db_session, test_node):
    """Test updating job status (callback from agent)."""
    from nexus.core.db import create_job
    from nexus.shared.models import JobCreate
    
    job_data = JobCreate(
        type=JobType.SHELL,
        node_id=test_node.id,
        payload={"command": "ls"}
    )
    job = create_job(db_session, job_data)
    
    payload = {
        "status": "completed",
        "result": {"output": "hello world", "success": True}
    }
    
    response = client.patch(f"/api/jobs/{job.id}", json=payload)
    assert response.status_code == 200
    
    # Verify DB update
    db_session.refresh(job)
    assert job.status == JobStatus.COMPLETED
    assert job.result["output"] == "hello world"
