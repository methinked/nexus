"""
Shell command executor for Nexus Agent.

Executes shell commands as jobs and captures output.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from nexus.shared import JobResult

logger = logging.getLogger(__name__)


class ShellExecutor:
    """
    Executes shell commands as jobs.

    Runs commands in a subprocess and captures stdout/stderr.
    """

    async def execute(self, payload: Dict) -> JobResult:
        """
        Execute a shell command.

        Args:
            payload: Job payload containing:
                - command: Shell command to execute
                - working_dir: Optional working directory
                - env: Optional environment variables
                - timeout: Optional timeout in seconds (default: 300)

        Returns:
            JobResult with command output

        Raises:
            asyncio.TimeoutError: If command exceeds timeout
        """
        command = payload.get("command")
        if not command:
            return JobResult(
                success=False,
                error="No command specified in payload",
            )

        working_dir = payload.get("working_dir")
        env = payload.get("env", {})
        timeout = payload.get("timeout", 300)  # Default 5 minutes

        logger.info(f"Executing shell command: {command}")
        start_time = datetime.utcnow()

        try:
            # Create subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env=env if env else None,
            )

            # Wait for completion with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )

            # Decode output
            stdout_str = stdout.decode("utf-8") if stdout else ""
            stderr_str = stderr.decode("utf-8") if stderr else ""

            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            # Check exit code
            success = process.returncode == 0

            if success:
                logger.info(f"Command completed successfully in {execution_time:.2f}s")
                return JobResult(
                    success=True,
                    output=stdout_str,
                    data={
                        "exit_code": process.returncode,
                        "stderr": stderr_str,
                        "execution_time": execution_time,
                    },
                )
            else:
                logger.warning(f"Command failed with exit code {process.returncode}")
                return JobResult(
                    success=False,
                    output=stdout_str,
                    error=f"Command exited with code {process.returncode}",
                    data={
                        "exit_code": process.returncode,
                        "stderr": stderr_str,
                        "execution_time": execution_time,
                    },
                )

        except asyncio.TimeoutError:
            logger.error(f"Command timed out after {timeout}s")
            try:
                process.kill()
                await process.wait()
            except Exception as e:
                logger.error(f"Error killing timed out process: {e}")

            return JobResult(
                success=False,
                error=f"Command timed out after {timeout} seconds",
                data={"timeout": timeout},
            )

        except Exception as e:
            logger.error(f"Error executing command: {e}", exc_info=True)
            return JobResult(
                success=False,
                error=f"Execution error: {str(e)}",
            )
