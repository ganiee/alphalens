"""FastAPI dependencies for authentication and authorization."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from adapters.cache import NoOpCache, ProviderCache, SqliteProviderCache
from adapters.cognito_auth import CognitoAuthVerifier
from adapters.fmp_fundamentals import FMPFundamentalsProvider
from adapters.http_client import RetryingHttpClient
from adapters.mock_auth import MockAuthVerifier
from adapters.mock_fundamentals import MockFundamentalsProvider
from adapters.mock_market_data import MockMarketDataProvider
from adapters.mock_news import MockNewsProvider
from adapters.mock_sentiment import MockSentimentAnalyzer
from adapters.newsapi_news import NewsAPINewsProvider
from adapters.polygon_market_data import PolygonMarketDataProvider
from domain.auth import AuthenticationError, AuthVerifier, TokenPayload, User
from domain.settings import Settings, get_settings
from repo.recommendations import RecommendationRepository, get_recommendation_repository
from services.recommendation import RecommendationService

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


@lru_cache
def get_provider_cache() -> ProviderCache:
    """Get the provider cache based on settings.

    Returns:
        ProviderCache implementation (SQLite or NoOp)
    """
    settings = get_settings()
    if not settings.provider_cache_enabled or settings.provider_cache_backend == "none":
        return NoOpCache()
    return SqliteProviderCache(
        db_path=settings.provider_cache_db_path,
        cache_dir=settings.provider_cache_dir,
    )


@lru_cache
def get_http_client() -> RetryingHttpClient:
    """Get a shared HTTP client instance.

    Returns:
        Configured RetryingHttpClient instance
    """
    settings = get_settings()
    return RetryingHttpClient(
        timeout_seconds=settings.http_timeout_seconds,
        max_retries=settings.http_max_retries,
        retry_backoff_seconds=settings.http_retry_backoff_seconds,
    )


def get_recommendation_service() -> RecommendationService:
    """Get the recommendation service with all dependencies.

    Uses real providers when API keys are configured, falls back to mock providers otherwise.

    Returns:
        Configured RecommendationService instance
    """
    settings = get_settings()
    cache = get_provider_cache()
    http_client = get_http_client()

    # Market data provider
    if settings.polygon_api_key:
        market_data = PolygonMarketDataProvider(
            api_key=settings.polygon_api_key,
            http_client=http_client,
            cache=cache,
            cache_ttl_seconds=settings.market_cache_ttl_seconds,
        )
    else:
        market_data = MockMarketDataProvider()

    # Fundamentals provider
    if settings.fmp_api_key:
        fundamentals = FMPFundamentalsProvider(
            api_key=settings.fmp_api_key,
            http_client=http_client,
            cache=cache,
            cache_ttl_seconds=settings.fundamentals_cache_ttl_seconds,
        )
    else:
        fundamentals = MockFundamentalsProvider()

    # News provider
    if settings.news_api_key:
        news = NewsAPINewsProvider(
            api_key=settings.news_api_key,
            http_client=http_client,
            cache=cache,
            cache_ttl_seconds=settings.news_cache_ttl_seconds,
            base_url=settings.news_api_base_url,
            page_size=settings.news_api_page_size,
        )
    else:
        news = MockNewsProvider()

    # Sentiment is always mock (keyword-based analysis)
    sentiment = MockSentimentAnalyzer()

    return RecommendationService(
        market_data=market_data,
        fundamentals=fundamentals,
        news=news,
        sentiment=sentiment,
    )


# Type alias for recommendation dependencies
RecommendationServiceDep = Annotated[RecommendationService, Depends(get_recommendation_service)]
RecommendationRepoDep = Annotated[RecommendationRepository, Depends(get_recommendation_repository)]
