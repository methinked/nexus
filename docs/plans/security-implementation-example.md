# Security Implementation Example

This document shows how to secure Nexus API endpoints with JWT authentication.

## Before: Insecure Endpoint

```python
# ❌ INSECURE - Anyone can submit metrics
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from nexus.core.db import create_metric, get_db
from nexus.shared import MetricCreate, BaseResponse

router = APIRouter()

@router.post("/api/metrics", response_model=BaseResponse)
async def submit_metrics(
    metric: MetricCreate,
    db: Session = Depends(get_db),
):
    """Submit metrics from agent."""
    create_metric(db, metric)
    return BaseResponse(message="Metrics received")
```

**Problem:** Any client on the network can:
- Submit fake metrics for any node
- Flood the system with data
- Corrupt monitoring data

## After: Secured Endpoint

```python
# ✅ SECURE - Only authenticated nodes can submit their own metrics
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from nexus.core.api.dependencies import verify_jwt_token
from nexus.core.db import create_metric, get_db
from nexus.shared import MetricCreate, BaseResponse, TokenData

router = APIRouter()

@router.post("/api/metrics", response_model=BaseResponse)
async def submit_metrics(
    metric: MetricCreate,
    db: Session = Depends(get_db),
    token_data: TokenData = Depends(verify_jwt_token),  # ← ADDED
):
    """
    Submit metrics from agent.

    Requires: Valid JWT token in Authorization header
    """
    # Verify node is submitting its own metrics (not another node's)
    if metric.node_id != token_data.node_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Node {token_data.node_name} cannot submit metrics for node {metric.node_id}",
        )

    create_metric(db, metric)
    return BaseResponse(message="Metrics received")
```

**Benefits:**
- ✅ Only authenticated nodes can submit
- ✅ Nodes can only submit their own metrics
- ✅ Token expiration enforced
- ✅ Invalid tokens rejected

## Agent-Side: Sending Authenticated Requests

The agent already has the token from registration. It just needs to include it:

```python
# Agent sends metrics with JWT token
import httpx

async def send_metrics(metric_data: dict, api_token: str, core_url: str):
    """Send metrics to Core with authentication."""

    # Add Authorization header with token
    headers = {
        "Authorization": f"Bearer {api_token}",  # ← Add this
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{core_url}/api/metrics",
            json=metric_data,
            headers=headers,  # ← Include headers
        )
        response.raise_for_status()
```

## Quick Migration Checklist

To secure an endpoint:

1. **Import the dependency:**
   ```python
   from nexus.core.api.dependencies import verify_jwt_token
   from nexus.shared import TokenData
   ```

2. **Add to function signature:**
   ```python
   async def my_endpoint(
       # ... existing parameters ...
       token_data: TokenData = Depends(verify_jwt_token),  # ← Add this
   ):
   ```

3. **Verify ownership (if node-specific):**
   ```python
   if resource.node_id != token_data.node_id:
       raise HTTPException(403, "Cannot access other node's resources")
   ```

4. **Update agent clients to send token:**
   ```python
   headers = {"Authorization": f"Bearer {api_token}"}
   ```

## Endpoints That Need Securing

### High Priority (P0)
- ✅ `/api/metrics` (POST) - Metrics submission
- ✅ `/api/terminal/{node_id}` (WebSocket) - Terminal access
- ✅ `/api/nodes/{node_id}` (PUT/DELETE) - Node modification
- ✅ `/api/jobs` (POST) - Job submission
- ✅ `/api/nodes/{node_id}/health` (GET) - Health data

### Medium Priority (P1)
- `/api/jobs/{id}` (GET) - Job details
- `/api/metrics/{node_id}` (GET) - Historical metrics
- `/api/metrics/{node_id}/stats` (GET) - Metric stats

### Low Priority (P2)
- `/api/nodes` (GET) - List nodes (might allow public read)
- `/health` (GET) - Health check (should stay public)

## WebSocket Authentication Example

WebSockets need special handling:

### Before: Insecure WebSocket

```python
@router.websocket("/terminal/{node_id}")
async def terminal_proxy(websocket: WebSocket, node_id: UUID):
    await websocket.accept()  # ❌ Anyone can connect!
    # ... terminal code ...
```

### After: Secured WebSocket

```python
from fastapi import Query

@router.websocket("/terminal/{node_id}")
async def terminal_proxy(
    websocket: WebSocket,
    node_id: UUID,
    token: str = Query(...),  # ← Token as query parameter
    config: CoreConfig = Depends(get_config),
):
    """
    WebSocket terminal proxy with authentication.

    Connect with: ws://host/api/terminal/{node_id}?token=<jwt_token>
    """
    # Verify token BEFORE accepting connection
    try:
        token_data = verify_token(token, config.jwt_secret_key, config.jwt_algorithm)
    except (TokenExpiredError, TokenInvalidError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Verify node ownership
    if str(node_id) != str(token_data.node_id):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Now safe to accept
    await websocket.accept()
    # ... terminal code ...
```

**Client connection:**
```python
import websockets

async def connect_terminal(node_id: str, token: str):
    uri = f"ws://core:8000/api/terminal/{node_id}?token={token}"
    async with websockets.connect(uri) as websocket:
        # Connected and authenticated
        pass
```

## Testing Authenticated Endpoints

### With curl:

```bash
# Get token (from agent_state.json or registration)
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Test authenticated request
curl -X POST http://localhost:8000/api/metrics \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"node_id": "...", "cpu_percent": 10.0, ...}'

# Test without token (should fail with 401)
curl -X POST http://localhost:8000/api/metrics \
  -H "Content-Type: application/json" \
  -d '{"node_id": "...", "cpu_percent": 10.0, ...}'
```

### With httpx (Python):

```python
import httpx

token = "eyJ..."  # Your JWT token

headers = {"Authorization": f"Bearer {token}"}

async with httpx.AsyncClient() as client:
    # Authenticated request
    response = await client.post(
        "http://localhost:8000/api/metrics",
        headers=headers,
        json=metric_data
    )
    print(response.status_code)  # Should be 200/201
```

## Common Issues

### Issue: "Missing Authorization header"
**Cause:** Client not sending token
**Fix:** Add `Authorization: Bearer <token>` header

### Issue: "Token has expired"
**Cause:** Token older than 24 hours
**Fix:** Re-register node or implement token refresh

### Issue: "Cannot access other node's resources"
**Cause:** Token's node_id doesn't match resource's node_id
**Fix:** Ensure client is using correct token for the node

### Issue: WebSocket closes immediately
**Cause:** Invalid or missing token in query parameter
**Fix:** Include `?token=<jwt>` in WebSocket URL

---

## Next Steps

1. **Implement P0 endpoints** - Start with metrics and terminal
2. **Test with real agent** - Verify agent can authenticate
3. **Add rate limiting** - Prevent brute force
4. **Enable HTTPS** - Encrypt all communication
5. **Audit logging** - Track authentication events

See [SECURITY.md](../SECURITY.md) for full security roadmap.
