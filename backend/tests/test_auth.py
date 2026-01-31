"""Tests for authentication functionality (F1-1)."""

import pytest
from fastapi.testclient import TestClient

from adapters.mock_auth import MockAuthVerifier
from domain.auth import AuthenticationError, TokenPayload, UserPlan, UserRole
from main import app

client = TestClient(app)


class TestTokenPayload:
    """Tests for TokenPayload entity."""

    def test_to_user_basic(self):
        """Basic user conversion sets default role and plan."""
        payload = TokenPayload(
            sub="user-123",
            email="test@example.com",
            email_verified=True,
            cognito_groups=[],
        )
        user = payload.to_user()

        assert user.sub == "user-123"
        assert user.email == "test@example.com"
        assert user.email_verified is True
        assert user.roles == [UserRole.USER]
        assert user.plan == UserPlan.FREE

    def test_to_user_with_admin_group(self):
        """Admin group adds admin role."""
        payload = TokenPayload(
            sub="admin-456",
            email="admin@example.com",
            email_verified=True,
            cognito_groups=["admin"],
        )
        user = payload.to_user()

        assert UserRole.ADMIN in user.roles
        assert UserRole.USER in user.roles
        assert user.is_admin is True

    def test_to_user_with_pro_group(self):
        """Pro group sets pro plan."""
        payload = TokenPayload(
            sub="pro-789",
            email="pro@example.com",
            email_verified=True,
            cognito_groups=["pro"],
        )
        user = payload.to_user()

        assert user.plan == UserPlan.PRO
        assert user.is_admin is False

    def test_to_user_with_multiple_groups(self):
        """Multiple groups are processed correctly."""
        payload = TokenPayload(
            sub="super-user",
            email="super@example.com",
            email_verified=True,
            cognito_groups=["admin", "pro"],
        )
        user = payload.to_user()

        assert user.is_admin is True
        assert user.plan == UserPlan.PRO


class TestMockAuthVerifier:
    """Tests for MockAuthVerifier adapter."""

    @pytest.fixture
    def verifier(self):
        """Create mock auth verifier."""
        return MockAuthVerifier()

    @pytest.mark.asyncio
    async def test_valid_user_token(self, verifier):
        """Valid user token returns correct payload."""
        payload = await verifier.verify_token(MockAuthVerifier.VALID_USER_TOKEN)

        assert payload.sub == "test-user-123"
        assert payload.email == "user@example.com"
        assert payload.cognito_groups == []

    @pytest.mark.asyncio
    async def test_valid_admin_token(self, verifier):
        """Valid admin token includes admin group."""
        payload = await verifier.verify_token(MockAuthVerifier.VALID_ADMIN_TOKEN)

        assert payload.sub == "test-admin-456"
        assert "admin" in payload.cognito_groups

    @pytest.mark.asyncio
    async def test_valid_pro_token(self, verifier):
        """Valid pro token includes pro group."""
        payload = await verifier.verify_token(MockAuthVerifier.VALID_PRO_TOKEN)

        assert "pro" in payload.cognito_groups

    @pytest.mark.asyncio
    async def test_expired_token_raises(self, verifier):
        """Expired token raises AuthenticationError."""
        with pytest.raises(AuthenticationError) as exc_info:
            await verifier.verify_token(MockAuthVerifier.EXPIRED_TOKEN)

        assert "expired" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_invalid_token_raises(self, verifier):
        """Invalid token raises AuthenticationError."""
        with pytest.raises(AuthenticationError):
            await verifier.verify_token(MockAuthVerifier.INVALID_TOKEN)

    @pytest.mark.asyncio
    async def test_unknown_token_raises(self, verifier):
        """Unknown token raises AuthenticationError."""
        with pytest.raises(AuthenticationError):
            await verifier.verify_token("some-random-token")


class TestAuthEndpoints:
    """Integration tests for auth endpoints using mock adapter."""

    def test_me_without_token_returns_401(self):
        """Missing authorization header returns 401."""
        response = client.get("/auth/me")

        assert response.status_code == 401
        assert "Missing authorization" in response.json()["detail"]

    def test_me_with_invalid_token_returns_401(self):
        """Invalid token returns 401."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401

    def test_me_with_valid_user_token(self):
        """Valid user token returns user info."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {MockAuthVerifier.VALID_USER_TOKEN}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "user@example.com"
        assert data["roles"] == ["user"]
        assert data["plan"] == "free"

    def test_me_with_valid_admin_token(self):
        """Valid admin token returns admin info."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {MockAuthVerifier.VALID_ADMIN_TOKEN}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "admin" in data["roles"]
        assert "user" in data["roles"]

    def test_me_with_valid_pro_token(self):
        """Valid pro token returns pro plan."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {MockAuthVerifier.VALID_PRO_TOKEN}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["plan"] == "pro"

    def test_admin_check_without_admin_role_returns_403(self):
        """Non-admin user gets 403 on admin endpoint."""
        response = client.get(
            "/auth/admin/check",
            headers={"Authorization": f"Bearer {MockAuthVerifier.VALID_USER_TOKEN}"},
        )

        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

    def test_admin_check_with_admin_role(self):
        """Admin user can access admin endpoint."""
        response = client.get(
            "/auth/admin/check",
            headers={"Authorization": f"Bearer {MockAuthVerifier.VALID_ADMIN_TOKEN}"},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Admin access confirmed"

    def test_health_endpoint_still_public(self):
        """Health endpoint remains accessible without auth."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
