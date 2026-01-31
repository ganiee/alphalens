"""Mock authentication adapter for testing."""

from domain.auth import AuthenticationError, TokenPayload


class MockAuthVerifier:
    """Mock auth verifier for testing purposes.

    This adapter allows testing without connecting to Cognito.
    It accepts specially formatted test tokens.
    """

    # Test tokens for different scenarios
    VALID_USER_TOKEN = "test-user-token"
    VALID_ADMIN_TOKEN = "test-admin-token"
    VALID_PRO_TOKEN = "test-pro-token"
    EXPIRED_TOKEN = "expired-token"
    INVALID_TOKEN = "invalid-token"

    # Predefined test users
    TEST_USERS = {
        VALID_USER_TOKEN: TokenPayload(
            sub="test-user-123",
            email="user@example.com",
            email_verified=True,
            cognito_groups=[],
        ),
        VALID_ADMIN_TOKEN: TokenPayload(
            sub="test-admin-456",
            email="admin@example.com",
            email_verified=True,
            cognito_groups=["admin"],
        ),
        VALID_PRO_TOKEN: TokenPayload(
            sub="test-pro-789",
            email="pro@example.com",
            email_verified=True,
            cognito_groups=["pro"],
        ),
    }

    async def verify_token(self, token: str) -> TokenPayload:
        """Verify mock token and return payload.

        Args:
            token: Mock token string

        Returns:
            TokenPayload for the test user

        Raises:
            AuthenticationError: If token is not a valid test token
        """
        if token == self.EXPIRED_TOKEN:
            raise AuthenticationError("Token has expired")

        if token == self.INVALID_TOKEN:
            raise AuthenticationError("Invalid token")

        if token in self.TEST_USERS:
            return self.TEST_USERS[token]

        raise AuthenticationError("Invalid token")
