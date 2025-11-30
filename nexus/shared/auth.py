"""
Shared authentication utilities for Nexus.

Provides JWT token creation, validation, and other auth helpers.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from nexus.shared.models import TokenData

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthError(Exception):
    """Base authentication error."""

    pass


class TokenExpiredError(AuthError):
    """Token has expired."""

    pass


class TokenInvalidError(AuthError):
    """Token is invalid."""

    pass


def create_access_token(
    node_id: UUID,
    node_name: str,
    secret_key: str,
    algorithm: str = "HS256",
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, datetime]:
    """
    Create a JWT access token for a node.

    Args:
        node_id: UUID of the node
        node_name: Name of the node
        secret_key: Secret key for signing
        algorithm: JWT algorithm (default: HS256)
        expires_delta: Token expiration time (default: 24 hours)

    Returns:
        Tuple of (token_string, expiration_datetime)
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=24)

    expire = datetime.utcnow() + expires_delta

    to_encode = {
        "node_id": str(node_id),
        "node_name": node_name,
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt, expire


def verify_token(token: str, secret_key: str, algorithm: str = "HS256") -> TokenData:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string
        secret_key: Secret key for verification
        algorithm: JWT algorithm (default: HS256)

    Returns:
        TokenData object with decoded information

    Raises:
        TokenExpiredError: If token has expired
        TokenInvalidError: If token is invalid
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])

        node_id_str: str = payload.get("node_id")
        if node_id_str is None:
            raise TokenInvalidError("Token missing node_id")

        node_name: str = payload.get("node_name")
        if node_name is None:
            raise TokenInvalidError("Token missing node_name")

        # Parse expiration
        exp_timestamp = payload.get("exp")
        exp = datetime.fromtimestamp(exp_timestamp) if exp_timestamp else None

        # Check if expired
        if exp and exp < datetime.utcnow():
            raise TokenExpiredError("Token has expired")

        return TokenData(
            node_id=UUID(node_id_str),
            node_name=node_name,
            exp=exp,
        )

    except JWTError as e:
        raise TokenInvalidError(f"Invalid token: {str(e)}")


def verify_shared_secret(provided_secret: str, expected_secret: str) -> bool:
    """
    Verify a shared secret.

    Args:
        provided_secret: Secret provided by agent
        expected_secret: Expected secret from config

    Returns:
        True if secrets match, False otherwise
    """
    return provided_secret == expected_secret


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)
