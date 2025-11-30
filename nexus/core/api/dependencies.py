"""
FastAPI dependencies for authentication and authorization.

Provides reusable dependency functions for protecting endpoints.
"""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from nexus.shared import CoreConfig, TokenData, TokenExpiredError, TokenInvalidError, verify_token


def get_config() -> CoreConfig:
    """Get CoreConfig instance."""
    return CoreConfig()


async def verify_jwt_token(
    authorization: Annotated[str, Header()] = None,
    config: CoreConfig = Depends(get_config),
) -> TokenData:
    """
    Verify JWT token from Authorization header.

    Extracts and validates the JWT token from the Authorization header.
    Used as a dependency to protect endpoints.

    Args:
        authorization: Authorization header value (format: "Bearer <token>")
        config: CoreConfig instance

    Returns:
        TokenData with node_id and node_name

    Raises:
        401: Missing, invalid, or expired token

    Example:
        @router.get("/protected")
        async def protected_endpoint(
            token_data: TokenData = Depends(verify_jwt_token)
        ):
            # token_data.node_id and token_data.node_name available here
            pass
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    # Verify and decode token
    try:
        token_data = verify_token(
            token=token,
            secret_key=config.jwt_secret_key,
            algorithm=config.jwt_algorithm,
        )
        return token_data

    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_optional_jwt_token(
    authorization: Annotated[str, Header()] = None,
    config: CoreConfig = Depends(get_config),
) -> TokenData | None:
    """
    Optional JWT token verification.

    Same as verify_jwt_token but returns None if no token provided.
    Useful for endpoints that have different behavior for authenticated vs unauthenticated users.

    Args:
        authorization: Authorization header value (optional)
        config: CoreConfig instance

    Returns:
        TokenData if valid token provided, None otherwise

    Example:
        @router.get("/optional-auth")
        async def optional_auth_endpoint(
            token_data: TokenData | None = Depends(verify_optional_jwt_token)
        ):
            if token_data:
                # Authenticated user
                pass
            else:
                # Unauthenticated user
                pass
    """
    if not authorization:
        return None

    try:
        return await verify_jwt_token(authorization, config)
    except HTTPException:
        return None
