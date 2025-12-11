"""
Update API routes for Nexus Core.

Handles OTA updates for agents.
"""

import io
import os
import tarfile
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from nexus.core.db.database import get_db
from nexus.core.db.crud import create_job
from nexus.shared.models import JobType, UpdateJobPayload, BaseResponse
from nexus.core.db import get_node

router = APIRouter()


def create_source_bundle() -> io.BytesIO:
    """
    Create a tarball of the current source code.
    
    Excludes venv, .git, __pycache__, and other artifacts.
    """
    exclude_dirs = {"venv", ".git", "__pycache__", ".idea", ".vscode", "data", "logs", "artifacts", ".gemini"}
    exclude_files = {".env", "agent.log", "nexus.db"}
    
    # Assuming code is running from project root or installed location
    # We want to package the 'nexus' directory and requirements.txt
    # Root is up 3 levels from here: nexus/core/api/update.py -> nexus/core/api -> nexus/core -> nexus -> PROJECT_ROOT
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for root, dirs, files in os.walk(base_dir):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file in exclude_files:
                    continue
                
                # Check extension exclusions
                if file.endswith(".pyc") or file.endswith(".db"):
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, base_dir)
                
                # Only include relevant paths (nexus/ package, scripts/, setup scripts, requirements)
                if rel_path.startswith("nexus/") or rel_path.startswith("scripts/") or rel_path in ["requirements.txt", "setup.py"]:
                    tar.add(full_path, arcname=rel_path)
                    
    buffer.seek(0)
    return buffer


@router.get("/bundle", response_class=StreamingResponse)
async def get_update_bundle():
    """Download the latest code bundle."""
    buffer = create_source_bundle()
    return StreamingResponse(
        buffer,
        media_type="application/gzip",
        headers={"Content-Disposition": "attachment; filename=nexus-update.tar.gz"}
    )


@router.post("/nodes/{node_id}/update", response_model=BaseResponse)
async def trigger_update(
    node_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Trigger an update for a specific node.
    
    Creates an UPDATE job on the node.
    """
    node = get_node(db, str(node_id))
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {node_id} not found"
        )
        
    # Construct download URL (assuming Core is accessible via the same host requesting this)
    # In production, this should be configurable. For now, we assume standard port.
    # We can't easily guess the external URL, so we might need to rely on agent config or a new setting.
    # HACK: Use a placeholder or configured URL. Since agents know CORE_URL, we can send a relative path?
    # No, agent needs full URL usually.
    # But wait, `UpdateJobPayload` asks for `download_url`.
    # If the agent is polling *this* core, it knows the core URL.
    # Let's send a relative path and let the agent prepend its configured CORE_URL.
    
    payload = UpdateJobPayload(
        version="latest", # TODO: Implement versioning
        download_url="/api/update/bundle",
        restart_service=True
    )
    
    create_job(
        db,
        node_id=str(node_id),
        type=JobType.UPDATE,
        payload=payload.model_dump()
    )
    
    return BaseResponse(message="Update job created")
