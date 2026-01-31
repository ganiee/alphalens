"""FastAPI dependencies for authentication and authorization."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from adapters.cognito_auth import CognitoAuthVerifier
from adapters.mock_auth import MockAuthVerifier
from domain.auth import AuthenticationError, AuthVerifier, TokenPayload, User
from domain.settings import Settings, get_settings

# Security scheme for OpenAPI docs
security = HTTPBearer(auto_error=False)


def get_auth_verifier(settings: Annotated[Settings, Depends(get_settings)]) -> AuthVerifier:
    """Get the appropriate auth verifier based on settings.

    Args:
        settings: Application settings

    Returns:
        AuthVerifier implementation (mock or Cognito)
    """
    if settings.auth_mode == "mock":
        return MockAuthVerifier()
    return CognitoAuthVerifier(settings)


async def get_token_payload(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    auth_verifier: Annotated[AuthVerifier, Depends(get_auth_verifier)],
) -> TokenPayload:
    """Extract and verify JWT token from Authorization header.

    Args:
        credentials: Bearer token from Authorization header
        auth_verifier: Auth verifier implementation

    Returns:
        Verified token payload

    Raises:
        HTTPException: 401 if token is missing or invalid
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return await auth_verifier.verify_token(credentials.credentials)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e.message),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_current_user(
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> User:
    """Get current authenticated user from token.

    Args:
        token_payload: Verified token payload

    Returns:
        User entity with roles and plan
    """
    return token_payload.to_user()


async def require_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require admin role for access.

    Args:
        user: Current authenticated user

    Returns:
        User if they have admin role

    Raises:
        HTTPException: 403 if user is not admin
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


# Type aliases for cleaner route signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_admin)]
