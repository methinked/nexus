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
        Execute update process via git pull script.
        """
        try:
            # Parse payload
            data = UpdateJobPayload(**payload)
            
            script_path = "nexus/agent/scripts/update_agent.sh"
            if not os.path.exists(script_path):
                # Fallback check
                script_path = "./nexus/agent/scripts/update_agent.sh"
                
            if not os.path.exists(script_path):
                 return JobResult(
                    success=False,
                    error=f"Update script not found at {script_path}"
                )

            # Make executable
            os.chmod(script_path, 0o755)

            logger.info("Scheduling Agent Update via update_agent.sh...")
            
            # Spawn background process that sleeps then runs the script
            # This allows the agent to report 'success' to Core before being restarted
            subprocess.Popen(
                f"sleep 3 && {script_path} > update.log 2>&1",
                shell=True,
                stdin=None, stdout=None, stderr=None,
                close_fds=True,
                start_new_session=True # Detach from parent
            )
                
            return JobResult(
                success=True,
                output="Update scheduled. Agent will restart in 3 seconds.",
                data={"version": data.version}
            )

        except Exception as e:
            logger.error(f"Update failed: {e}", exc_info=True)
            return JobResult(
                success=False,
                error=str(e)
            )
