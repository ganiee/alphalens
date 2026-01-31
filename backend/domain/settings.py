"""Application settings and configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # AWS Cognito settings
    aws_region: str = "us-east-1"
    cognito_user_pool_id: str = ""
    cognito_client_id: str = ""
    cognito_domain: str = ""

    # Auth mode: "cognito" for production, "mock" for testing
    auth_mode: str = "cognito"

    # CORS settings - include multiple ports for local dev
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
    ]

    # Data Provider API Keys
    fmp_api_key: str = ""
    polygon_api_key: str = ""
    news_api_key: str = ""
    news_api_base_url: str = "https://newsapi.org/v2"
    news_api_country: str = "us"
    news_api_page_size: int = 8

    # Cache Configuration
    provider_cache_enabled: bool = True
    provider_cache_backend: str = "sqlite"
    provider_cache_dir: str = ".cache/alphalens"
    provider_cache_db_path: str = ".cache/alphalens/cache.sqlite"
    market_cache_ttl_seconds: int = 60
    fundamentals_cache_ttl_seconds: int = 86400
    news_cache_ttl_seconds: int = 300

    # HTTP Client Configuration
    http_timeout_seconds: int = 10
    http_max_retries: int = 2
    http_retry_backoff_seconds: float = 0.5

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def cognito_jwks_url(self) -> str:
        """URL for Cognito JWKS (JSON Web Key Set)."""
        return (
            f"https://cognito-idp.{self.aws_region}.amazonaws.com/"
            f"{self.cognito_user_pool_id}/.well-known/jwks.json"
        )

    @property
    def cognito_issuer(self) -> str:
        """Expected issuer for JWT tokens."""
        return f"https://cognito-idp.{self.aws_region}.amazonaws.com/{self.cognito_user_pool_id}"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
