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

### WebSocket Endpoints

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
