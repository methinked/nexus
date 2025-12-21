"""
Docker container management service.

Handles Docker operations on the agent node including:
- Container lifecycle (pull, create, start, stop, restart, remove)
- Container status monitoring
- Container logs retrieval
"""

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

import docker
from docker.errors import DockerException, NotFound, APIError
from docker.models.containers import Container

logger = logging.getLogger(__name__)


class DockerService:
    """
    Service for managing Docker containers on the agent.

    Uses the Docker SDK to interact with the local Docker daemon.
    """

    def __init__(self):
        """Initialize Docker client."""
        self.client: Optional[docker.DockerClient] = None
        self._connect()

    def _connect(self):
        """Connect to the local Docker daemon."""
        # Try standard methods first (env vars, default socket)
        try:
            self.client = docker.from_env()
            self.client.ping()
            logger.info("Successfully connected to Docker daemon via from_env()")
            return
        except DockerException:
            pass

        # Start looking for alternative sockets
        common_paths = [
            "unix:///var/run/docker.sock",
            f"unix:///run/user/{os.getuid()}/docker.sock"
        ]

        # Check for non-standard user sockets (e.g. if running as root but accessing user docker)
        # This is a bit of a guess, but helpful for some setups
        if os.path.exists("/run/user/1000/docker.sock"):
             common_paths.append("unix:///run/user/1000/docker.sock")

        for path in common_paths:
            try:
                logger.debug(f"Attempting connection to {path}")
                self.client = docker.DockerClient(base_url=path)
                self.client.ping()
                logger.info(f"Successfully connected to Docker daemon at {path}")
                return
            except DockerException as e:
                logger.debug(f"Failed to connect to {path}: {e}")

        logger.error("Failed to connect to Docker daemon using any method")
        self.client = None

    def is_available(self) -> bool:
        """Check if Docker is available."""
        if not self.client:
            self._connect()
        return self.client is not None

    def pull_image(self, image: str) -> bool:
        """
        Pull a Docker image.

        Args:
            image: Image name with optional tag (e.g., "nginx:latest")

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            logger.error("Docker is not available")
            return False

        try:
            logger.info(f"Pulling image: {image}")
            self.client.images.pull(image)
            logger.info(f"Successfully pulled image: {image}")
            return True
        except Exception as e:
            logger.error(f"Failed to pull image {image}: {e}")
            return False

    def create_container(
        self,
        deployment_id: str,
        image: str,
        name: Optional[str] = None,
        ports: Optional[Dict[int, int]] = None,
        volumes: Optional[Dict[str, Dict[str, str]]] = None,
        environment: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Optional[str]:
        """
        Create a Docker container.

        Args:
            deployment_id: Deployment ID for labeling
            image: Docker image to use
            name: Container name (optional)
            ports: Port mappings {container_port: host_port}
            volumes: Volume mappings {host_path: {'bind': container_path, 'mode': 'rw'}}
            environment: Environment variables
            **kwargs: Additional docker.containers.create() arguments

        Returns:
            Container ID if successful, None otherwise
        """
        if not self.is_available():
            logger.error("Docker is not available")
            return None

        # Pull image first
        if not self.pull_image(image):
            return None

        try:
            # Add Nexus labels
            labels = kwargs.get('labels', {})
            labels.update({
                'nexus.deployment_id': deployment_id,
                'nexus.managed': 'true',
                'nexus.created_at': datetime.utcnow().isoformat()
            })
            kwargs['labels'] = labels

            # Create container
            container = self.client.containers.create(
                image=image,
                name=name,
                ports=ports,
                volumes=volumes,
                environment=environment,
                detach=True,
                **kwargs
            )

            logger.info(f"Created container {container.id[:12]} for deployment {deployment_id}")
            return container.id

        except Exception as e:
            logger.error(f"Failed to create container: {e}")
            return None

    def start_container(self, container_id: str) -> bool:
        """
        Start a container.

        Args:
            container_id: Container ID or name

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False

        try:
            container = self.client.containers.get(container_id)
            container.start()
            logger.info(f"Started container {container_id[:12]}")
            return True
        except NotFound:
            logger.error(f"Container {container_id} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to start container {container_id}: {e}")
            return False

    def stop_container(self, container_id: str, timeout: int = 10) -> bool:
        """
        Stop a container.

        Args:
            container_id: Container ID or name
            timeout: Seconds to wait before killing

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False

        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=timeout)
            logger.info(f"Stopped container {container_id[:12]}")
            return True
        except NotFound:
            logger.error(f"Container {container_id} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to stop container {container_id}: {e}")
            return False

    def restart_container(self, container_id: str, timeout: int = 10) -> bool:
        """
        Restart a container.

        Args:
            container_id: Container ID or name
            timeout: Seconds to wait before killing

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False

        try:
            container = self.client.containers.get(container_id)
            container.restart(timeout=timeout)
            logger.info(f"Restarted container {container_id[:12]}")
            return True
        except NotFound:
            logger.error(f"Container {container_id} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to restart container {container_id}: {e}")
            return False

    def remove_container(self, container_id: str, force: bool = False) -> bool:
        """
        Remove a container.

        Args:
            container_id: Container ID or name
            force: Force removal even if running

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False

        try:
            container = self.client.containers.get(container_id)
            container.remove(force=force)
            logger.info(f"Removed container {container_id[:12]}")
            return True
        except NotFound:
            logger.error(f"Container {container_id} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to remove container {container_id}: {e}")
            return False

    def get_container_status(self, container_id: str) -> Optional[Dict[str, Any]]:
        """
        Get container status and info.

        Args:
            container_id: Container ID or name

        Returns:
            Container status dict or None if not found
        """
        if not self.is_available():
            return None

        try:
            container = self.client.containers.get(container_id)
            container.reload()  # Refresh container data

            return {
                'id': container.id,
                'name': container.name,
                'status': container.status,  # created, running, exited, etc.
                'image': container.image.tags[0] if container.image.tags else container.image.id,
                'created': container.attrs['Created'],
                'started_at': container.attrs['State'].get('StartedAt'),
                'finished_at': container.attrs['State'].get('FinishedAt'),
                'exit_code': container.attrs['State'].get('ExitCode'),
                'error': container.attrs['State'].get('Error'),
                'labels': container.labels
            }
        except NotFound:
            return None
        except Exception as e:
            logger.error(f"Failed to get container status: {e}")
            return None

    def get_container_description(self, container: Container) -> str:
        """
        Get a friendly description for the container.
        
        Checks labels for common metadata.
        """
        labels = container.labels or {}
        
        # 1. Check OCI standard description
        if "org.opencontainers.image.description" in labels:
            return labels["org.opencontainers.image.description"]
            
        # 2. Check generic description
        if "description" in labels:
            return labels["description"]
            
        # 3. Check Docker Compose service name
        if "com.docker.compose.service" in labels:
            return f"Service: {labels['com.docker.compose.service']}"
            
        # 4. Fallback to image name (cleaned up)
        image_tag = container.image.tags[0] if container.image.tags else ""
        if image_tag:
            return image_tag
            
        # 5. Last resort: Image ID partial
        return f"Image: {container.image.id[:12]}"

    def list_containers(self, all_containers: bool = False) -> List[Dict[str, Any]]:
        """
        List containers.

        Args:
            all_containers: If True, list all containers. If False, list only Nexus-managed.

        Returns:
            List of container status dicts
        """
        if not self.is_available():
            return []

        try:
            filters = {}
            if not all_containers:
                filters = {'label': 'nexus.managed=true'}

            containers = self.client.containers.list(
                all=True,
                filters=filters
            )

            results = []
            for c in containers:
                # Calculate Uptime / Started At
                started_at = c.attrs.get("State", {}).get("StartedAt")
                
                # Parse ports
                ports = []
                port_bindings = c.attrs.get("NetworkSettings", {}).get("Ports") or {}
                for internal, bindings in port_bindings.items():
                    if bindings:
                        for b in bindings:
                            host_port = b.get('HostPort', '')
                            if host_port:
                                ports.append(f"{host_port}:{internal}")
                    else:
                        ports.append(internal)

                results.append({
                    'id': c.id,
                    'short_id': c.short_id,
                    'name': c.name,
                    'status': c.status,
                    'state': c.attrs.get("State", {}).get("Status", "unknown"),
                    'image': c.image.tags[0] if c.image.tags else (c.image.id if c.image else "unknown"),
                    'deployment_id': c.labels.get('nexus.deployment_id'),
                    'managed': c.labels.get('nexus.managed') == 'true',
                    'created_at': c.attrs['Created'],
                    'started_at': started_at,
                    'ports': ", ".join(ports),
                    'description': self.get_container_description(c)
                })
            
            return results
        except Exception as e:
            logger.error(f"Failed to list containers: {e}")
            return []

    def get_container_logs(self, container_id: str, tail: int = 100) -> Optional[str]:
        """
        Get container logs.

        Args:
            container_id: Container ID or name
            tail: Number of lines to retrieve

        Returns:
            Log output as string or None if not found
        """
        if not self.is_available():
            return None

        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail, timestamps=True)
            return logs.decode('utf-8', errors='ignore')
        except NotFound:
            return None
        except Exception as e:
            logger.error(f"Failed to get container logs: {e}")
            return None

    def get_container_stats(self, container_id: str) -> Optional[Dict[str, Any]]:
        """
        Get container resource usage stats.

        Args:
            container_id: Container ID or name

        Returns:
            Stats dict with CPU and memory usage or None if not found
        """
        if not self.is_available():
            return None

        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)

            # Calculate CPU percentage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            cpu_percent = 0.0
            if system_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage'].get('percpu_usage', [])) * 100

            # Calculate memory usage
            mem_usage = stats['memory_stats'].get('usage', 0)
            mem_limit = stats['memory_stats'].get('limit', 1)
            mem_percent = (mem_usage / mem_limit) * 100 if mem_limit > 0 else 0

            return {
                'cpu_percent': round(cpu_percent, 2),
                'memory_usage_bytes': mem_usage,
                'memory_limit_bytes': mem_limit,
                'memory_percent': round(mem_percent, 2)
            }
        except NotFound:
            return None
        except Exception as e:
            logger.error(f"Failed to get container stats: {e}")
            return None
