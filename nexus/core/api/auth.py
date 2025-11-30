"""
Authentication API routes for Nexus Core.

Handles node registration and token management.
"""

from datetime import timedelta
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from nexus.shared import (
    CoreConfig,
    RegistrationRequest,
    RegistrationResponse,
    Token,
    create_access_token,
    verify_shared_secret,
)

router = APIRouter()
config = CoreConfig()


@router.post("/register", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_node(request: RegistrationRequest):
    """
    Register a new agent node.

    The agent provides a shared secret for authentication. If valid, the Core
    issues a unique API token that the agent uses for all future requests.

    Args:
        request: Registration request with shared secret and node info

    Returns:
        Registration response with node_id and API token

    Raises:
        401: Invalid shared secret
        409: Node already registered (TODO: implement duplicate check)
    """
    # Verify shared secret
    if not verify_shared_secret(request.shared_secret, config.shared_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid shared secret",
        )

    # TODO: Check if node already exists in database
    # TODO: Store node in database

    # Generate new node ID
    node_id = uuid4()

    # Create API token
    token, expires_at = create_access_token(
        node_id=node_id,
        node_name=request.name,
        secret_key=config.jwt_secret_key,
        algorithm=config.jwt_algorithm,
        expires_delta=timedelta(hours=config.jwt_expiration_hours),
    )

    # TODO: Store node registration in database with token info

    return RegistrationResponse(
        node_id=node_id,
        api_token=token,
        expires_at=expires_at,
    )


@router.post("/token/refresh", response_model=Token)
async def refresh_token():
    """
    Refresh an expiring API token.

    Requires valid current token in Authorization header.

    Returns:
        New token with updated expiration

    Raises:
        401: Invalid or expired token
    """
    # TODO: Implement token refresh
    # TODO: Verify current token from Authorization header
    # TODO: Generate new token
    # TODO: Update token in database

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Token refresh not yet implemented",
    )
