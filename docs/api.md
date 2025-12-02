# Nexus API Documentation

## Overview

Nexus uses FastAPI for both Core and Agent APIs. All endpoints use JSON for request/response bodies.

**Base URLs:**
- Core: `http://core-host:8000/api`
- Agent: `http://agent-host:8001/api`

**Authentication:** Bearer token (JWT) in Authorization header

---

## Core API

### Health & Status

#### `GET /health`

Health check endpoint (no auth required).

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime": 3600
}
```

---

### Authentication

#### `POST /api/auth/register`

Register a new agent node.

**Request:**
```json
{
  "shared_secret": "pre-shared-key",
  "node_name": "kitchen-pi",
  "ip_address": "192.168.1.100",
  "metadata": {
    "location": "kitchen",
    "tags": ["camera"]
  }
}
```

**Response:**
```json
{
  "node_id": "uuid",
  "api_token": "jwt-token",
  "expires_at": "timestamp"
}
```

**Errors:**
- `401 Unauthorized` - Invalid shared secret
- `409 Conflict` - Node already registered

---

#### `POST /api/auth/token/refresh`

Refresh an expiring API token.

**Headers:**
```
Authorization: Bearer <current-token>
```

**Response:**
```json
{
  "api_token": "new-jwt-token",
  "expires_at": "timestamp"
}
```

---

### Node Management

#### `GET /api/nodes`

List all registered nodes.

**Query Parameters:**
- `status` (optional): Filter by status (online, offline, error)
- `tag` (optional): Filter by metadata tag

**Response:**
```json
{
  "nodes": [
    {
      "id": "uuid",
      "name": "kitchen-pi",
      "ip_address": "192.168.1.100",
      "status": "online",
      "last_seen": "timestamp",
      "metadata": {...}
    }
  ],
  "total": 1
}
```

---

#### `GET /api/nodes/{node_id}`

Get detailed status of a specific node.

**Response:**
```json
{
  "id": "uuid",
  "name": "kitchen-pi",
  "ip_address": "192.168.1.100",
  "status": "online",
  "last_seen": "timestamp",
  "metadata": {...},
  "current_metrics": {
    "cpu_percent": 45.2,
    "memory_percent": 62.1,
    "disk_percent": 38.5,
    "temperature": 52.3
  },
  "active_jobs": 2
}
```

---

#### `PUT /api/nodes/{node_id}`

Update node metadata.

**Request:**
```json
{
  "name": "kitchen-pi-v2",
  "metadata": {
    "location": "new-kitchen",
    "tags": ["camera", "ocr"]
  }
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "kitchen-pi-v2",
  "updated_at": "timestamp"
}
```

---

#### `DELETE /api/nodes/{node_id}`

Deregister a node.

**Response:**
```json
{
  "message": "Node deregistered successfully"
}
```

---

### Job Management

#### `POST /api/jobs`

Submit a new job.

**Request:**
```json
{
  "type": "ocr",
  "node_id": "uuid",
  "payload": {
    "file_path": "/path/to/image.jpg",
    "language": "eng"
  }
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "pending",
  "created_at": "timestamp"
}
```

---

#### `GET /api/jobs`

List all jobs.

**Query Parameters:**
- `node_id` (optional): Filter by node
- `status` (optional): Filter by status
- `type` (optional): Filter by job type

**Response:**
```json
{
  "jobs": [
    {
      "id": "uuid",
      "type": "ocr",
      "node_id": "uuid",
      "status": "completed",
      "created_at": "timestamp",
      "completed_at": "timestamp"
    }
  ],
  "total": 1
}
```

---

#### `GET /api/jobs/{job_id}`

Get job details and result.

**Response:**
```json
{
  "id": "uuid",
  "type": "ocr",
  "node_id": "uuid",
  "status": "completed",
  "payload": {...},
  "result": {
    "output_path": "/vault/notes/2024-01-15.md",
    "text_extracted": true
  },
  "created_at": "timestamp",
  "completed_at": "timestamp"
}
```

---

### Metrics

#### `POST /api/metrics`

Submit metrics from agent (agent-facing).

**Request:**
```json
{
  "node_id": "uuid",
  "timestamp": "timestamp",
  "cpu_percent": 45.2,
  "memory_percent": 62.1,
  "disk_percent": 38.5,
  "temperature": 52.3
}
```

**Response:**
```json
{
  "received": true
}
```

---

#### `GET /api/metrics/{node_id}`

Get historical metrics for a node.

**Query Parameters:**
- `start_time` (optional): Start timestamp
- `end_time` (optional): End timestamp
- `interval` (optional): Aggregation interval (1m, 5m, 1h)

**Response:**
```json
{
  "node_id": "uuid",
  "metrics": [
    {
      "timestamp": "timestamp",
      "cpu_percent": 45.2,
      "memory_percent": 62.1,
      "disk_percent": 38.5,
      "temperature": 52.3
    }
  ]
}
```

---

#### `GET /api/metrics/{node_id}/stats`

Get aggregated statistics for a node's metrics.

**Query Parameters:**
- `start_time` (optional): Start timestamp
- `end_time` (optional): End timestamp

**Response:**
```json
{
  "node_id": "uuid",
  "stats": {
    "cpu_percent": {
      "min": 10.5,
      "max": 95.2,
      "avg": 45.3
    },
    "memory_percent": {
      "min": 40.1,
      "max": 85.6,
      "avg": 62.4
    },
    "disk_percent": {
      "min": 35.0,
      "max": 42.1,
      "avg": 38.5
    },
    "temperature": {
      "min": 45.0,
      "max": 65.3,
      "avg": 52.8
    }
  },
  "period": {
    "start": "timestamp",
    "end": "timestamp",
    "count": 120
  }
}
```

---

#### `GET /api/nodes/{node_id}/health`

Get health status for a node with threshold evaluation.

**Response:**
```json
{
  "node_id": "uuid",
  "status": "warning",
  "metrics": {
    "cpu_percent": 45.2,
    "memory_percent": 82.1,
    "disk_percent": 38.5,
    "temperature": 52.3
  },
  "thresholds": {
    "cpu": {"warning": 80, "critical": 95},
    "memory": {"warning": 80, "critical": 95},
    "disk": {"warning": 85, "critical": 95},
    "temperature": {"warning": 70, "critical": 85}
  },
  "warnings": [
    "Memory usage is at 82.1% (warning threshold: 80%)"
  ],
  "last_updated": "timestamp"
}
```

---

### Logs

#### `POST /api/logs`

Submit logs from agent (agent-facing).

**Request:**
```json
{
  "node_id": "uuid",
  "level": "info",
  "message": "Agent started successfully",
  "timestamp": "timestamp",
  "metadata": {
    "component": "agent.core"
  }
}
```

**Response:**
```json
{
  "received": true
}
```

---

#### `GET /api/logs`

Get logs from all nodes.

**Query Parameters:**
- `node_id` (optional): Filter by specific node
- `level` (optional): Filter by log level (debug, info, warning, error)
- `start_time` (optional): Start timestamp
- `end_time` (optional): End timestamp
- `limit` (optional): Max number of logs to return (default: 100)

**Response:**
```json
{
  "logs": [
    {
      "id": "uuid",
      "node_id": "uuid",
      "node_name": "kitchen-pi",
      "level": "info",
      "message": "Metrics collected successfully",
      "timestamp": "timestamp",
      "metadata": {}
    }
  ],
  "total": 1
}
```

---

#### `GET /api/logs/{node_id}`

Get logs for a specific node.

**Query Parameters:**
- `level` (optional): Filter by log level
- `start_time` (optional): Start timestamp
- `end_time` (optional): End timestamp
- `limit` (optional): Max number of logs (default: 100)

**Response:**
```json
{
  "node_id": "uuid",
  "node_name": "kitchen-pi",
  "logs": [
    {
      "id": "uuid",
      "level": "info",
      "message": "Agent heartbeat sent",
      "timestamp": "timestamp",
      "metadata": {}
    }
  ],
  "total": 1
}
```

---

### Services (Docker Orchestration)

#### `GET /api/services`

List all service templates.

**Response:**
```json
{
  "services": [
    {
      "id": "uuid",
      "name": "pihole",
      "image": "pihole/pihole:latest",
      "description": "Network-wide ad blocking",
      "ports": [{"host": 80, "container": 80}],
      "volumes": [{"host": "/data/pihole", "container": "/etc/pihole"}],
      "environment": {"TZ": "America/New_York"},
      "created_at": "timestamp"
    }
  ],
  "total": 1
}
```

---

#### `GET /api/services/{service_id}`

Get details of a specific service template.

**Response:**
```json
{
  "id": "uuid",
  "name": "pihole",
  "image": "pihole/pihole:latest",
  "description": "Network-wide ad blocking",
  "ports": [{"host": 80, "container": 80}],
  "volumes": [{"host": "/data/pihole", "container": "/etc/pihole"}],
  "environment": {"TZ": "America/New_York"},
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

---

#### `POST /api/services`

Create a new service template.

**Request:**
```json
{
  "name": "pihole",
  "image": "pihole/pihole:latest",
  "description": "Network-wide ad blocking",
  "ports": [{"host": 80, "container": 80}],
  "volumes": [{"host": "/data/pihole", "container": "/etc/pihole"}],
  "environment": {"TZ": "America/New_York"}
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "pihole",
  "created_at": "timestamp"
}
```

---

#### `PUT /api/services/{service_id}`

Update a service template.

**Request:**
```json
{
  "name": "pihole-updated",
  "description": "Updated description",
  "environment": {"TZ": "Europe/London"}
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "pihole-updated",
  "updated_at": "timestamp"
}
```

---

#### `DELETE /api/services/{service_id}`

Delete a service template.

**Response:**
```json
{
  "message": "Service deleted successfully"
}
```

---

### Deployments (Docker Orchestration)

#### `GET /api/deployments`

List all deployments.

**Query Parameters:**
- `node_id` (optional): Filter by node
- `status` (optional): Filter by status (pending, running, stopped, failed)

**Response:**
```json
{
  "deployments": [
    {
      "id": "uuid",
      "service_id": "uuid",
      "service_name": "pihole",
      "node_id": "uuid",
      "node_name": "kitchen-pi",
      "status": "running",
      "created_at": "timestamp"
    }
  ],
  "total": 1
}
```

---

#### `GET /api/deployments/{deployment_id}`

Get details of a specific deployment.

**Response:**
```json
{
  "id": "uuid",
  "service_id": "uuid",
  "service_name": "pihole",
  "node_id": "uuid",
  "node_name": "kitchen-pi",
  "status": "running",
  "config": {
    "ports": [{"host": 80, "container": 80}],
    "volumes": [{"host": "/data/pihole", "container": "/etc/pihole"}],
    "environment": {"TZ": "America/New_York"}
  },
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "started_at": "timestamp"
}
```

---

#### `POST /api/deployments`

Create a new deployment.

**Request:**
```json
{
  "service_id": "uuid",
  "node_id": "uuid",
  "config": {
    "environment": {"CUSTOM_VAR": "value"}
  }
}
```

**Response:**
```json
{
  "id": "uuid",
  "service_id": "uuid",
  "node_id": "uuid",
  "status": "pending",
  "created_at": "timestamp"
}
```

---

#### `PUT /api/deployments/{deployment_id}`

Update deployment configuration.

**Request:**
```json
{
  "config": {
    "environment": {"TZ": "Europe/London"}
  }
}
```

**Response:**
```json
{
  "id": "uuid",
  "updated_at": "timestamp"
}
```

---

#### `POST /api/deployments/{deployment_id}/start`

Start a deployment.

**Response:**
```json
{
  "id": "uuid",
  "status": "running",
  "started_at": "timestamp"
}
```

---

#### `POST /api/deployments/{deployment_id}/stop`

Stop a deployment.

**Response:**
```json
{
  "id": "uuid",
  "status": "stopped",
  "stopped_at": "timestamp"
}
```

---

#### `POST /api/deployments/{deployment_id}/restart`

Restart a deployment.

**Response:**
```json
{
  "id": "uuid",
  "status": "running",
  "restarted_at": "timestamp"
}
```

---

#### `DELETE /api/deployments/{deployment_id}`

Delete a deployment (stops and removes).

**Response:**
```json
{
  "message": "Deployment deleted successfully"
}
```

---

### WebSocket Endpoints

#### `WS /api/ws`

General WebSocket endpoint for real-time updates.

**Auth:** Token in query parameter: `?token=<jwt>`

**Server -> Client Messages:**
```json
// Metrics update
{
  "type": "metrics",
  "node_id": "uuid",
  "data": {
    "cpu_percent": 45.2,
    "memory_percent": 62.1,
    "disk_percent": 38.5,
    "temperature": 52.3
  }
}

// Node status change
{
  "type": "node_status",
  "node_id": "uuid",
  "status": "online"
}

// Deployment status change
{
  "type": "deployment_status",
  "deployment_id": "uuid",
  "status": "running"
}
```

---

#### `WS /api/nodes/{node_id}/terminal`

Open a WebSocket terminal session to a node.

**Auth:** Token in query parameter: `?token=<jwt>`

**Messages:**
```json
// Client -> Server
{"type": "input", "data": "ls -la\n"}

// Server -> Client
{"type": "output", "data": "total 48\ndrwxr-xr-x..."}
```

---

## Agent API

### Health & Status

#### `GET /health`

Health check (no auth required).

**Response:**
```json
{
  "status": "healthy",
  "node_id": "uuid",
  "version": "0.1.0"
}
```

---

### Job Execution

#### `POST /api/jobs/{job_id}/execute`

Execute a job (called by Core).

**Request:**
```json
{
  "type": "ocr",
  "payload": {
    "file_path": "/path/to/image.jpg",
    "language": "eng"
  }
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "running",
  "started_at": "timestamp"
}
```

---

#### `GET /api/jobs/{job_id}/status`

Get job execution status.

**Response:**
```json
{
  "job_id": "uuid",
  "status": "completed",
  "result": {
    "output_path": "/vault/notes/output.md"
  },
  "started_at": "timestamp",
  "completed_at": "timestamp"
}
```

---

### System Info

#### `GET /api/system/info`

Get system information.

**Response:**
```json
{
  "hostname": "kitchen-pi",
  "os": "Raspbian GNU/Linux 11",
  "kernel": "5.10.63-v7l+",
  "architecture": "armv7l",
  "cpu_count": 4,
  "total_memory": 4096,
  "total_disk": 32000
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {...}
  }
}
```

**Common HTTP Status Codes:**
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict
- `500 Internal Server Error` - Server error

---

## Rate Limiting

- **Metrics submission:** 1 request per 10 seconds per node
- **Job submission:** 10 requests per minute
- **General API:** 100 requests per minute per token

Exceeding limits returns `429 Too Many Requests`.

---

## Versioning

API version is specified in the URL path: `/api/v1/...`

Current version: `v1` (implicit, can omit for now)

---

## OpenAPI Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI:** `http://core-host:8000/docs`
- **ReDoc:** `http://core-host:8000/redoc`
- **OpenAPI JSON:** `http://core-host:8000/openapi.json`
