"""Cognito authentication adapter for production use."""

import logging
import time
from typing import Any

import httpx
from jose import JWTError, jwt

from domain.auth import AuthenticationError, TokenPayload
from domain.settings import Settings

logger = logging.getLogger(__name__)


class CognitoAuthVerifier:
    """Cognito JWT verification adapter.

    This adapter verifies JWT tokens issued by Amazon Cognito.
    It caches the JWKS for performance.
    """

    def __init__(self, settings: Settings):
        """Initialize with settings.

        Args:
            settings: Application settings with Cognito configuration
        """
        self.settings = settings
        self._jwks: dict[str, Any] | None = None
        self._jwks_fetched_at: float = 0
        self._jwks_cache_seconds = 3600  # Cache JWKS for 1 hour

    async def _get_jwks(self) -> dict[str, Any]:
        """Fetch and cache JWKS from Cognito.

        Returns:
            JWKS dictionary with signing keys

        Raises:
            AuthenticationError: If JWKS cannot be fetched
        """
        now = time.time()

        # Return cached JWKS if still valid
        if self._jwks and (now - self._jwks_fetched_at) < self._jwks_cache_seconds:
            return self._jwks

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.settings.cognito_jwks_url)
                response.raise_for_status()
                self._jwks = response.json()
                self._jwks_fetched_at = now
                return self._jwks
        except httpx.HTTPError as e:
            raise AuthenticationError(f"Failed to fetch JWKS: {e}") from e

    def _get_signing_key(self, jwks: dict[str, Any], kid: str) -> dict[str, Any]:
        """Find the signing key matching the token's key ID.

        Args:
            jwks: JWKS dictionary
            kid: Key ID from token header

        Returns:
            Key dictionary for signature verification

        Raises:
            AuthenticationError: If key is not found
        """
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key
        raise AuthenticationError("Signing key not found")

    async def verify_token(self, token: str) -> TokenPayload:
        """Verify Cognito JWT token and return payload.

        Supports both access tokens (have client_id claim) and ID tokens (have aud claim).

        Args:
            token: JWT access token or ID token from Authorization header

        Returns:
            TokenPayload with user information

        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            logger.info("verify_token: Starting token verification")
            logger.debug(f"verify_token: Token prefix: {token[:50]}...")

            # Get unverified header to find key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            logger.info(f"verify_token: Token kid: {kid}")
            if not kid:
                raise AuthenticationError("Token missing key ID")

            # Get JWKS and find signing key
            jwks = await self._get_jwks()
            signing_key = self._get_signing_key(jwks, kid)
            logger.info("verify_token: Found signing key")

            # Verify and decode token
            # Note: Cognito access tokens don't have 'aud' claim, they have 'client_id'
            # So we disable audience verification and verify client_id manually
            # Also disable at_hash verification since we're not providing the access_token
            logger.info(f"verify_token: Expected issuer: {self.settings.cognito_issuer}")
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                issuer=self.settings.cognito_issuer,
                options={
                    "verify_aud": False,  # Access tokens don't have aud
                    "verify_iss": True,
                    "verify_exp": True,
                    "verify_at_hash": False,  # Skip at_hash verification for ID tokens
                },
            )
            logger.info(f"verify_token: Token decoded successfully, claims: {list(payload.keys())}")

            # Verify client_id for access tokens or aud for ID tokens
            token_client_id = payload.get("client_id") or payload.get("aud")
            expected_client_id = self.settings.cognito_client_id
            logger.info(
                f"verify_token: client_id/aud: {token_client_id}, "
                f"expected: {expected_client_id}"
            )
            if token_client_id != expected_client_id:
                raise AuthenticationError(
                    f"Invalid token: client_id mismatch "
                    f"(expected {expected_client_id}, got {token_client_id})"
                )

            # Extract user information from token
            # Access tokens have 'username' and 'sub', ID tokens have 'email' etc.
            email = payload.get("email", payload.get("username", ""))
            logger.info(f"verify_token: Extracted email: {email}, sub: {payload.get('sub')}")

            return TokenPayload(
                sub=payload.get("sub", ""),
                email=email,
                email_verified=payload.get("email_verified", False),
                cognito_groups=payload.get("cognito:groups", []),
            )

        except JWTError as e:
            logger.error(f"verify_token: JWT error: {e}")
            raise AuthenticationError(f"Invalid token: {e}") from e
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"verify_token: Unexpected error: {e}")
            raise AuthenticationError(f"Token verification failed: {e}") from e
