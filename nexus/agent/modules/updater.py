"""
Update executor for Nexus Agent.

Handles downloading code updates and restarting the service.
"""

import io
import logging
import os
import subprocess
import tarfile
import httpx

from nexus.shared.models import UpdateJobPayload, JobResult

logger = logging.getLogger(__name__)


class UpdateExecutor:
    """Executes update jobs."""

    def __init__(self, core_url: str, api_token: str):
        self.core_url = core_url.rstrip("/")
        self.api_token = api_token

    async def execute(self, payload: dict) -> JobResult:
        """
        Execute update process.

        Args:
            payload: UpdateJobPayload data

        Returns:
            JobResult indicating success/failure
        """
        try:
            # Parse payload
            data = UpdateJobPayload(**payload)
            
            # Construct full download URL
            # If payload.download_url is relative, append to core_url
            download_url = data.download_url
            if not download_url.startswith("http"):
                download_url = f"{self.core_url}/{download_url.lstrip('/')}"
            
            logger.info(f"Downloading update from {download_url}...")
            
            # Download bundle
            headers = {"Authorization": f"Bearer {self.api_token}"}
            async with httpx.AsyncClient() as client:
                response = await client.get(download_url, headers=headers, follow_redirects=True, timeout=60.0)
                response.raise_for_status()
                content = response.content
                
            logger.info(f"Downloaded {len(content)} bytes. Extracting...")
            
            # Extract tarball
            # We assume we are running from the project root or we know where to extract
            # Standard deployment: /home/methinked/Projects/nexus/nexus (or similar)
            # We will extract to the CURRENT working directory
            extract_path = os.getcwd()
            
            # Backup current version? (Enhancement)
            
            with tarfile.open(fileobj=io.BytesIO(content), mode="r:gz") as tar:
                # Security check (prevent path traversal)
                for member in tar.getmembers():
                    if member.name.startswith("/") or ".." in member.name:
                        raise ValueError(f"Malicious path in tarball: {member.name}")
                tar.extractall(path=extract_path)
                
            logger.info("Extraction complete.")
            
            # Install dependencies
            logger.info("Installing dependencies...")
            subprocess.run(
                ["venv/bin/pip", "install", "-r", "requirements.txt"],
                check=True,
                capture_output=True
            )
            
            # Restart service if requested
            if data.restart_service:
                logger.info("Restarting agent service...")
                # We use 'nohup' and a shell command to ensure the restart continues 
                # even if this process dies immediately.
                # However, running 'systemctl restart' from inside the service kills it instantly.
                # We need to fork or return 'success' first, THEN die.
                # But if we die, we can't report success.
                # Strategy:
                # 1. Return JobResult success.
                # 2. Schedule restart in a detached process/Timer
                
                # We will handle the actual restart in the dispatcher AFTER reporting results?
                # Or just fire and forget here?
                # Systemctl restart blocks until done? No, it kills the process.
                
                # Let's spawn a background shell command that waits a few seconds then restarts
                subprocess.Popen(
                    "sleep 5 && sudo systemctl restart nexus-agent",
                    shell=True,
                    stdin=None, stdout=None, stderr=None,
                    close_fds=True
                )
                
            return JobResult(
                success=True,
                output="Update downloaded and extracted. Service restart scheduled.",
                data={"version": data.version}
            )

        except Exception as e:
            logger.error(f"Update failed: {e}", exc_info=True)
            return JobResult(
                success=False,
                error=str(e)
            )
