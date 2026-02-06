"""Domain entities for authentication."""

from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, EmailStr


class UserRole(StrEnum):
    """User roles in the system."""

    USER = "user"
    ADMIN = "admin"


class UserPlan(StrEnum):
    """User subscription plans."""

    FREE = "free"
    PRO = "pro"


class User(BaseModel):
    """Authenticated user entity."""

    sub: str  # Cognito subject (unique user ID)
    email: EmailStr
    email_verified: bool = False
    roles: list[UserRole] = [UserRole.USER]
    plan: UserPlan = UserPlan.FREE

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return UserRole.ADMIN in self.roles


class TokenPayload(BaseModel):
    """JWT token payload extracted from Cognito access token."""

    sub: str
    email: str
    email_verified: bool = False
    cognito_groups: list[str] = []

    def to_user(self) -> User:
        """Convert token payload to User entity."""
        roles = [UserRole.USER]
        plan = UserPlan.FREE

        # Map Cognito groups to roles and plans
        for group in self.cognito_groups:
            if group.lower() == "admin":
                roles.append(UserRole.ADMIN)
            elif group.lower() == "pro":
                plan = UserPlan.PRO

        return User(
            sub=self.sub,
            email=self.email,
            email_verified=self.email_verified,
            roles=roles,
            plan=plan,
        )


class AuthVerifier(Protocol):
    """Protocol for authentication verification (port)."""

    async def verify_token(self, token: str) -> TokenPayload:
        """Verify JWT token and return payload.

        Args:
            token: JWT access token from Authorization header

        Returns:
            TokenPayload with user information

        Raises:
            AuthenticationError: If token is invalid or expired
        """
        ...


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        self.message = message
        super().__init__(self.message)
