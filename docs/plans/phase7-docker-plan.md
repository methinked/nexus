# Phase 7: Docker Service Orchestration - Implementation Plan

**Version:** 1.0
**Date:** 2025-12-01
**Status:** Planning Phase

---

## 🎯 Overview

Phase 7 transforms Nexus from a monitoring and management platform into a **full fleet orchestration system** with Docker as the foundational technology. This enables users to deploy and manage containerized services (Pi-hole, Home Assistant, Prometheus, etc.) across their Debian-based fleet from a single interface.

---

## 🏗️ Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                    Nexus Core                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Service Catalog (Templates)                      │  │
│  │ - Pi-hole, Home Assistant, Prometheus, etc.      │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Service Deployment Manager                       │  │
│  │ - Parse Docker Compose YAML                      │  │
│  │ - Track deployment state                         │  │
│  │ - Send deployment jobs to agents                 │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Database (SQLite)                                │  │
│  │ - Service definitions                            │  │
│  │ - Deployment records                             │  │
│  │ - Container status per node                      │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          │ API/WebSocket
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    Agent Node                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Docker Module (nexus/agent/modules/docker.py)    │  │
│  │ - Uses Docker SDK for Python                     │  │
│  │ - Container lifecycle management                 │  │
│  │ - Health and resource monitoring                 │  │
│  └──────────────────────────────────────────────────┘  │
│                          │                              │
│                          │ Docker Socket API            │
│                          ▼                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Docker Daemon                                     │  │
│  │ - Container runtime                               │  │
│  │ - Image management                                │  │
│  │ - Network and volume handling                     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Data Models

### Service Model (Core)

```python
class Service(Base):
    """Service definition (template)"""
    id: UUID
    name: str  # e.g., "pihole"
    display_name: str  # e.g., "Pi-hole DNS"
    description: str
    version: str  # Docker image version
    category: str  # "networking", "monitoring", "automation", etc.
    docker_compose: str  # YAML content
    default_env: dict  # Default environment variables
    icon_url: str  # Icon for UI
    created_at: datetime
```

### Deployment Model (Core)

```python
class Deployment(Base):
    """Service deployment instance"""
    id: UUID
    service_id: UUID  # Foreign key to Service
    name: str  # User-defined deployment name
    node_id: UUID  # Foreign key to Node
    config: dict  # User-provided configuration (env vars, ports, etc.)
    status: DeploymentStatus  # DEPLOYING, RUNNING, STOPPED, FAILED
    container_id: str | None  # Docker container ID (from agent)
    deployed_at: datetime
    updated_at: datetime
```

### Container Status Model (Agent → Core)

```python
class ContainerStatus(BaseModel):
    """Container runtime status reported by agent"""
    deployment_id: UUID
    container_id: str
    status: str  # "running", "exited", "paused", etc.
    cpu_percent: float
    memory_usage: int  # bytes
    created_at: datetime
    started_at: datetime | None
    health: str | None  # "healthy", "unhealthy", "starting"
```

---

## 🔧 Implementation Tasks

### Phase 7.1: Core Service Management API

**Goal:** Add service and deployment models to Core database

**Tasks:**
1. Create database models
   - `ServiceModel` - Service templates
   - `DeploymentModel` - Deployment instances
   - `ContainerStatusModel` - Runtime status (optional: could use metrics)

2. Create Alembic migration
   - Add services, deployments tables
   - Foreign keys and indexes

3. Create CRUD operations
   - `create_service`, `get_service`, `list_services`, `delete_service`
   - `create_deployment`, `get_deployment`, `update_deployment_status`, `list_deployments`

4. Create API endpoints
   - `GET /api/services` - List available services
   - `GET /api/services/{id}` - Get service details
   - `POST /api/services` - Create custom service (admin)
   - `POST /api/deployments` - Deploy service to node(s)
   - `GET /api/deployments` - List all deployments
   - `GET /api/deployments/{id}` - Get deployment details
   - `DELETE /api/deployments/{id}` - Remove deployment
   - `POST /api/deployments/{id}/start` - Start container
   - `POST /api/deployments/{id}/stop` - Stop container
   - `POST /api/deployments/{id}/restart` - Restart container

**Estimated Effort:** 1-2 days

---

### Phase 7.2: Agent Docker Module

**Goal:** Enable agents to manage Docker containers

**Tasks:**
1. Install dependencies
   - Add `docker` to requirements-agent.txt
   - Update deployment script to install Docker if needed

2. Create Docker module
   - `nexus/agent/modules/docker.py`
   - Connect to Docker daemon (`/var/run/docker.sock`)
   - Functions:
     - `deploy_compose(compose_yaml, config)` - Deploy from compose
     - `start_container(container_id)`
     - `stop_container(container_id)`
     - `restart_container(container_id)`
     - `remove_container(container_id)`
     - `get_container_status(container_id)`
     - `stream_logs(container_id, since)`

3. Create Docker API endpoints on agent
   - `POST /api/docker/deploy` - Deploy container from compose
   - `POST /api/docker/{container_id}/start`
   - `POST /api/docker/{container_id}/stop`
   - `POST /api/docker/{container_id}/restart`
   - `DELETE /api/docker/{container_id}`
   - `GET /api/docker/{container_id}/status`
   - `GET /api/docker/{container_id}/logs`

4. Container health monitoring
   - Background task to monitor container status
   - Report container metrics to Core (CPU, memory per container)
   - Push status updates via existing metrics endpoint

**Estimated Effort:** 2-3 days

---

### Phase 7.3: Service Templates

**Goal:** Pre-built templates for common services

**Tasks:**
1. Create service template library
   - `nexus/core/templates/` directory
   - YAML files for each service:
     - `pihole.yaml` - Pi-hole DNS ad-blocker
     - `homeassistant.yaml` - Home Assistant
     - `prometheus.yaml` - Prometheus monitoring
     - `grafana.yaml` - Grafana dashboards
     - `portainer.yaml` - Portainer Docker UI
     - `nginx.yaml` - Nginx web server
     - `wireguard.yaml` - WireGuard VPN

2. Template structure
   ```yaml
   name: pihole
   display_name: Pi-hole DNS
   description: Network-wide ad blocking
   version: "5.18"
   category: networking
   icon_url: https://...
   docker_compose: |
     version: "3"
     services:
       pihole:
         image: pihole/pihole:5.18
         environment:
           - TZ=${TZ}
           - WEBPASSWORD=${WEBPASSWORD}
         ports:
           - "80:80"
           - "53:53/tcp"
           - "53:53/udp"
         restart: unless-stopped
   default_env:
     TZ: "UTC"
     WEBPASSWORD: "admin"
   ```

3. Template loader
   - Load templates into database on Core startup
   - Update templates when files change
   - Seed script for initial templates

**Estimated Effort:** 1 day

---

### Phase 7.4: Deployment Workflow

**Goal:** Implement end-to-end deployment flow

**Tasks:**
1. Core deployment logic
   - `nexus/core/services/deployment.py`
   - Parse user configuration (env vars, ports, volumes)
   - Merge with service template
   - Create deployment record in database
   - Send deployment job to agent

2. Agent deployment handler
   - Receive deployment job via existing job system
   - Call Docker module to deploy
   - Report success/failure back to Core
   - Update deployment status in Core database

3. Error handling
   - Image pull failures
   - Port conflicts
   - Volume mount errors
   - Container start failures
   - Rollback on failure

**Estimated Effort:** 2 days

---

### Phase 7.5: CLI Commands

**Goal:** Command-line interface for service management

**Tasks:**
1. Create service CLI commands
   - `nexus/cli/commands/service.py`
   - `nexus service list` - List available services
   - `nexus service show <name>` - Show service details
   - `nexus service deploy <name> --node <id> [--env KEY=VALUE]`
   - `nexus service deployments` - List all deployments
   - `nexus service start <deployment_id>`
   - `nexus service stop <deployment_id>`
   - `nexus service restart <deployment_id>`
   - `nexus service remove <deployment_id>`
   - `nexus service logs <deployment_id> [--follow]`

2. Rich formatting
   - Service catalog table
   - Deployment status table
   - Live log streaming (follow mode)

**Estimated Effort:** 1 day

---

### Phase 7.6: Web UI - Services Page

**Goal:** Web interface for Docker service management

**Tasks:**
1. Create services page template
   - `nexus/web/templates/services.html`
   - Service catalog grid (see dashboard-ui-plan.md)
   - Deployed services table
   - Deployment status badges

2. Deployment modal
   - Service selection
   - Node selection (single/multiple/all)
   - Configuration form (env vars, ports)
   - Advanced options (volumes, networks)
   - Deploy button

3. Service management
   - Per-deployment actions (start/stop/restart/remove)
   - Container logs viewer modal
   - Resource usage charts per container
   - Health status indicators

4. JavaScript interactions
   - Real-time status updates via WebSocket
   - Deployment wizard flow
   - Form validation
   - CLI view integration

**Estimated Effort:** 3-4 days

---

### Phase 7.7: Container Monitoring

**Goal:** Track container health and resource usage

**Tasks:**
1. Extend metrics collection
   - Add container-level metrics to agent
   - CPU, memory, network per container
   - Container status (running, stopped, exited)

2. Container metrics API
   - `GET /api/metrics/containers/{deployment_id}`
   - Historical container resource usage
   - Aggregated stats across nodes

3. Dashboard integration
   - Add container metrics to node detail view
   - Show per-container resource charts
   - Alert on container failures

**Estimated Effort:** 2 days

---

## 🗺️ Implementation Roadmap

### Week 1: Core Foundation
- Day 1-2: Phase 7.1 - Core Service Management API
- Day 3: Phase 7.3 - Service Templates
- Day 4-5: Phase 7.2 - Agent Docker Module (partial)

### Week 2: Agent Integration
- Day 1-2: Phase 7.2 - Agent Docker Module (complete)
- Day 3-4: Phase 7.4 - Deployment Workflow
- Day 5: Testing and bug fixes

### Week 3: User Interfaces
- Day 1: Phase 7.5 - CLI Commands
- Day 2-4: Phase 7.6 - Web UI Services Page
- Day 5: Phase 7.7 - Container Monitoring

### Week 4: Polish and Launch
- Day 1-2: Testing on real Raspberry Pi
- Day 3: Documentation updates
- Day 4: Example deployments and tutorials
- Day 5: Release Phase 7

**Total Estimated Effort:** 3-4 weeks

---

## 🧪 Testing Strategy

### Unit Tests
- Service CRUD operations
- Deployment state machine
- Docker module functions
- Template loading and validation

### Integration Tests
- End-to-end deployment flow
- Container lifecycle (deploy → start → stop → remove)
- Multi-node deployment
- Error handling and rollback

### Real-World Testing
- Deploy Pi-hole on Raspberry Pi
- Deploy Prometheus + Grafana stack
- Deploy Home Assistant on multiple nodes
- Test resource constraints (Pi 3 with 1GB RAM)
- Test network configurations

---

## 🔒 Security Considerations

1. **Docker Socket Access**
   - Agent needs access to `/var/run/docker.sock`
   - Run agent with appropriate permissions (docker group)
   - Consider security implications of Docker API access

2. **Container Isolation**
   - Use Docker user namespaces if possible
   - Limit container resources (CPU, memory)
   - Network segmentation for containers

3. **Secrets Management**
   - Environment variables for passwords (not ideal)
   - Future: Integrate with Docker secrets or HashiCorp Vault
   - Warn users about sensitive data in compose files

4. **Image Security**
   - Use official images from Docker Hub
   - Support custom registries for private images
   - Consider image scanning (future enhancement)

---

## 📚 Documentation Needs

1. **User Guide**
   - How to deploy your first service
   - Service catalog overview
   - Configuration examples
   - Troubleshooting common issues

2. **Admin Guide**
   - Creating custom service templates
   - Docker prerequisites per node
   - Security best practices
   - Resource planning

3. **Developer Guide**
   - Adding new service templates
   - Docker Compose YAML format
   - API reference for deployments

---

## 🎯 Success Metrics

Phase 7 is successful if:
1. User can deploy Pi-hole to a Pi with < 5 clicks
2. Service status updates in real-time on dashboard
3. Multi-node deployment works (e.g., Prometheus on all nodes)
4. Container logs accessible from web UI
5. Zero manual SSH required for service deployment
6. Works reliably on Raspberry Pi 3 (1GB RAM)

---

### Phase 7.8: Container Migration (Bonus Feature)

**Goal:** Move running containers between nodes with one click

**Use Cases:**
- Hardware upgrade (Pi 3 → Pi 4)
- Load balancing (move heavy service to more powerful node)
- Failure recovery (move from failing to healthy node)
- Maintenance (evacuate node before reboot)
- Optimization (co-locate related services)

**Tasks:**
1. Migration API
   - `POST /api/deployments/{id}/migrate` - Migrate to different node
   - Parameters: `target_node_id`, `keep_source` (default: false)
   - Response: Migration job ID

2. Migration workflow
   - Stop container on source node
   - Save volumes/config (if applicable)
   - Deploy to target node with identical configuration
   - Start container on target node
   - Verify health on target
   - Remove from source (unless keep_source=true)
   - Update deployment record in database

3. Web UI
   - "Migrate" button on deployment detail page
   - Node selector modal
   - Progress indicator
   - Rollback option if migration fails

4. CLI command
   - `nexus service migrate <deployment_id> --to <node_id>`
   - `--keep-source` flag for testing/blue-green

**Estimated Effort:** 2 days

**This is a killer feature - no other fleet management tool makes this so easy!**

---

## 🚀 Future Enhancements (Phase 8+)

- **Container Migration** - Move services between nodes with one click (Phase 7.8 above)
- **Docker Compose Stacks:** Deploy multi-container apps (e.g., WordPress + MySQL)
- **Service Discovery:** Auto-configure services to find each other
- **Load Balancing:** Distribute traffic across multiple instances
- **Auto-Scaling:** Deploy more instances based on load
- **Auto-Migration:** Automatically move services from unhealthy nodes
- **Kubernetes Support:** Optional K8s orchestration for advanced users
- **Private Registry:** Host custom images within Nexus
- **Backup/Restore:** Container volume backups and restoration

---

**End of Phase 7 Planning Document**
