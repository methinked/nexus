"""
Authentication API routes for Nexus Core.

Handles node registration and token management.
"""

from datetime import timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from nexus.core.db import create_node, get_node_by_name, get_user_by_username
from nexus.core.db.database import get_db
from nexus.shared import (
    CoreConfig,
    NodeCreate,
    RegistrationRequest,
    RegistrationResponse,
    Token,
    UserLoginRequest,
    create_access_token,
    verify_shared_secret,
    verify_password,
)

router = APIRouter()
config = CoreConfig()


@router.post("/register", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_node(
    request: RegistrationRequest,
    db: Session = Depends(get_db),
):
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
        409: Node already registered with same name
    """
    # Verify shared secret
    if not verify_shared_secret(request.shared_secret, config.shared_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid shared secret",
        )

    # Check if node with same name already exists
    # Check if node with same name already exists
    existing_node = get_node_by_name(db, request.name)
    if existing_node:
        # If node exists and shared secret is valid (already checked),
        # we treat this as a re-registration / recovery.
        # Update IP and metadata
        existing_node.ip_address = request.ip_address
        if request.metadata:
             existing_node.node_metadata = request.metadata.model_dump()
        
        db.commit()
        db.refresh(existing_node)
        
        # Create new API token
        token, expires_at = create_access_token(
            node_id=existing_node.id,
            node_name=existing_node.name,
            secret_key=config.jwt_secret_key,
            algorithm=config.jwt_algorithm,
            expires_delta=timedelta(hours=config.jwt_expiration_hours),
        )

        return RegistrationResponse(
            node_id=existing_node.id,
            api_token=token,
            expires_at=expires_at,
        )

    # Create node in database
    node_data = NodeCreate(
        name=request.name,
        ip_address=request.ip_address,
        shared_secret=request.shared_secret,
        metadata=request.metadata,
    )
    db_node = create_node(db, node_data)

    # Create API token
    token, expires_at = create_access_token(
        node_id=db_node.id,
        node_name=db_node.name,
        secret_key=config.jwt_secret_key,
        algorithm=config.jwt_algorithm,
        expires_delta=timedelta(hours=config.jwt_expiration_hours),
    )

    # Note: Token is stored on agent side, not in Core database
    # This allows for stateless authentication via JWT

    return RegistrationResponse(
        node_id=db_node.id,
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
@router.post("/login", response_model=Token)
async def login_user(
    request: UserLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate a user user and return a JWT token.
    """
    user = get_user_by_username(db, request.username)
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    token, expires_at = create_access_token(
        node_id=user.id,
        node_name=user.username,
        secret_key=config.jwt_secret_key,
        role=user.role,
        algorithm=config.jwt_algorithm,
        expires_delta=timedelta(hours=config.jwt_expiration_hours),
    )

    return Token(
        api_token=token,
        expires_at=expires_at,
    )
