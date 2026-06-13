"""
Users API routes for Nexus Core.

Handles user management and role assignments.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from nexus.core.api.dependencies import verify_admin, verify_jwt_token
from nexus.core.db.database import get_db
from nexus.shared.models import User, UserCreate, TokenData, UserRole

router = APIRouter()

from fastapi import Request

@router.post("", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_new_user(
    request: Request,
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new user. Only admins can create users, EXCEPT if there are no users in the database yet.
    """
    from nexus.core.db.crud import get_user_by_username, create_user
    from nexus.shared.auth import hash_password
    from nexus.core.db.models import UserModel
    from nexus.core.api.dependencies import verify_jwt_token, get_config
    
    # Check if this is the first user
    user_count = db.query(UserModel).count()
    if user_count > 0:
        # Require admin token
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        config = get_config()
        token_data = await verify_jwt_token(auth_header, config)
        if token_data.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Requires administrator privileges",
            )

    if get_user_by_username(db, user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
        
    hashed_pwd = hash_password(user_in.password)
    return create_user(db, user_in, hashed_pwd)


@router.get("", response_model=List[User])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    token_data: TokenData = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """
    List all users. Only admins can list users.
    """
    from nexus.core.db.models import UserModel
    
    users = db.query(UserModel).offset(skip).limit(limit).all()
    return users
