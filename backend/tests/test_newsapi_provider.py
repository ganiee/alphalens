"""Tests for the NewsAPI news provider."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from adapters.cache import CacheEntry
from adapters.newsapi_news import NewsAPINewsProvider
from domain.providers import ProviderError


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    return AsyncMock()


@pytest.fixture
def mock_cache():
    """Create a mock cache that returns None (cache miss)."""
    cache = MagicMock()
    cache.get.return_value = None
    return cache


@pytest.fixture
def newsapi_provider(mock_http_client, mock_cache):
    """Create a NewsAPI provider with mocked dependencies."""
    return NewsAPINewsProvider(
        api_key="test-api-key",
        http_client=mock_http_client,
        cache=mock_cache,
        cache_ttl_seconds=300,
        page_size=8,
    )


class TestNewsAPINewsProvider:
    """Tests for the NewsAPINewsProvider."""

    @pytest.mark.asyncio
    async def test_successful_fetch(self, newsapi_provider, mock_http_client, mock_cache):
        """Test successful news article fetch."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {
                    "title": "Apple stock surges on strong earnings",
                    "source": {"name": "Reuters"},
                    "publishedAt": "2024-01-15T10:30:00Z",
                    "url": "https://reuters.com/article1",
                    "description": "Apple reported record growth in quarterly earnings.",
                },
                {
                    "title": "Tech sector faces market concerns",
                    "source": {"name": "Bloomberg"},
                    "publishedAt": "2024-01-15T09:00:00Z",
                    "url": "https://bloomberg.com/article2",
                    "description": "Investors worry about tech valuations amid slowdown.",
                },
            ],
        }
        mock_http_client.get.return_value = mock_response

        result = await newsapi_provider.get_news("AAPL", max_articles=5)

        assert len(result) == 2
        assert result[0].title == "Apple stock surges on strong earnings"
        assert result[0].source == "Reuters"
        assert result[0].url == "https://reuters.com/article1"

        # Verify HTTP call - uses ticker + "stock" when no company_name provided
        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args[1]["headers"]["X-Api-Key"] == "test-api-key"
        assert call_args[1]["params"]["q"] == "AAPL stock"

        # Verify cache was updated
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_company_name(self, newsapi_provider, mock_http_client, mock_cache):
        """Test that search query uses company name when provided."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {
                    "title": "Apple Inc reports strong quarterly earnings",
                    "source": {"name": "Reuters"},
                    "publishedAt": "2024-01-15T10:30:00Z",
                    "url": "https://reuters.com/article1",
                    "description": "Apple reported record growth.",
                },
            ],
        }
        mock_http_client.get.return_value = mock_response

        result = await newsapi_provider.get_news(
            "AAPL", max_articles=5, company_name="Apple Inc."
        )

        assert len(result) == 1

        # Verify query uses cleaned company name with stock context
        call_args = mock_http_client.get.call_args
        query = call_args[1]["params"]["q"]
        assert '"Apple" AND (stock OR shares OR market)' == query

    @pytest.mark.asyncio
    async def test_search_company_name_same_as_ticker(
        self, newsapi_provider, mock_http_client, mock_cache
    ):
        """Test fallback to ticker query when company_name equals ticker."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [],
        }
        mock_http_client.get.return_value = mock_response

        await newsapi_provider.get_news("AAPL", max_articles=5, company_name="AAPL")

        # Should fall back to ticker-based query
        call_args = mock_http_client.get.call_args
        assert call_args[1]["params"]["q"] == "AAPL stock"

    @pytest.mark.asyncio
    async def test_fallback_to_ticker_when_company_name_returns_empty(
        self, newsapi_provider, mock_http_client, mock_cache
    ):
        """Test fallback to ticker search when company name search returns no results."""
        # First call (company name) returns empty, second call (ticker) returns results
        empty_response = MagicMock()
        empty_response.json.return_value = {"status": "ok", "articles": []}

        ticker_response = MagicMock()
        ticker_response.json.return_value = {
            "status": "ok",
            "articles": [
                {
                    "title": "GOOG stock rises",
                    "source": {"name": "Reuters"},
                    "publishedAt": "2024-01-15T10:00:00Z",
                    "url": "https://example.com/1",
                    "description": "Google parent company stock rises.",
                },
            ],
        }

        mock_http_client.get.side_effect = [empty_response, ticker_response]

        result = await newsapi_provider.get_news(
            "GOOG", max_articles=5, company_name="Alphabet Inc."
        )

        # Should have made two API calls
        assert mock_http_client.get.call_count == 2

        # First call should use company name
        first_call = mock_http_client.get.call_args_list[0]
        assert '"Alphabet" AND (stock OR shares OR market)' == first_call[1]["params"]["q"]

        # Second call should use ticker
        second_call = mock_http_client.get.call_args_list[1]
        assert second_call[1]["params"]["q"] == "GOOG stock"

        # Should return results from ticker search
        assert len(result) == 1
        assert result[0].title == "GOOG stock rises"

    @pytest.mark.asyncio
    async def test_sentiment_label_positive(self, newsapi_provider, mock_http_client, mock_cache):
        """Test sentiment labeling for positive news."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {
                    "title": "Apple stock surge as earnings beat expectations",
                    "source": {"name": "Reuters"},
                    "publishedAt": "2024-01-15T10:00:00Z",
                    "url": "https://example.com/1",
                    "description": "Record growth and strong profits reported.",
                },
            ],
        }
        mock_http_client.get.return_value = mock_response

        result = await newsapi_provider.get_news("AAPL")

        assert len(result) == 1
        assert result[0].sentiment_label == "positive"

    @pytest.mark.asyncio
    async def test_sentiment_label_negative(self, newsapi_provider, mock_http_client, mock_cache):
        """Test sentiment labeling for negative news."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {
                    "title": "Company stock crashes amid terrible scandal",
                    "source": {"name": "Bloomberg"},
                    "publishedAt": "2024-01-15T10:00:00Z",
                    "url": "https://example.com/1",
                    "description": "Worst earnings ever, investors flee in panic.",
                },
            ],
        }
        mock_http_client.get.return_value = mock_response

        result = await newsapi_provider.get_news("AAPL")

        assert len(result) == 1
        assert result[0].sentiment_label == "negative"

    @pytest.mark.asyncio
    async def test_sentiment_label_neutral(self, newsapi_provider, mock_http_client, mock_cache):
        """Test sentiment labeling for neutral news."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {
                    "title": "Company announces new product launch date",
                    "source": {"name": "TechCrunch"},
                    "publishedAt": "2024-01-15T10:00:00Z",
                    "url": "https://example.com/1",
                    "description": "The company will release their product next month.",
                },
            ],
        }
        mock_http_client.get.return_value = mock_response

        result = await newsapi_provider.get_news("AAPL")

        assert len(result) == 1
        assert result[0].sentiment_label == "neutral"

    @pytest.mark.asyncio
    async def test_returns_cached_data(self, mock_http_client):
        """Test that cached data is returned without API call."""
        cache = MagicMock()
        cached_entry = CacheEntry(
            cache_key="newsapi:news:AAPL:max_articles=5",
            provider="newsapi",
            data={
                "articles": [
                    {
                        "title": "Cached news article",
                        "source": "Reuters",
                        "published_at": "2024-01-15T10:00:00Z",
                        "url": "https://example.com/cached",
                        "summary": "Cached summary",
                        "sentiment_label": "positive",
                    }
                ]
            },
            ticker="AAPL",
            fetched_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        cache.get.return_value = cached_entry

        provider = NewsAPINewsProvider(
            api_key="test-key",
            http_client=mock_http_client,
            cache=cache,
        )

        result = await provider.get_news("AAPL", max_articles=5)

        assert len(result) == 1
        assert result[0].title == "Cached news article"
        assert result[0].sentiment_label == "positive"

        mock_http_client.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_api_error_response(self, newsapi_provider, mock_http_client):
        """Test handling of API error response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "error",
            "message": "API key invalid",
        }
        mock_http_client.get.return_value = mock_response

        with pytest.raises(ProviderError) as exc_info:
            await newsapi_provider.get_news("AAPL")

        assert exc_info.value.provider == "newsapi"
        assert "API key invalid" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_http_error(self, newsapi_provider, mock_http_client):
        """Test handling of HTTP errors."""
        mock_http_client.get.side_effect = httpx.HTTPError("Connection timeout")

        with pytest.raises(ProviderError) as exc_info:
            await newsapi_provider.get_news("AAPL")

        assert exc_info.value.provider == "newsapi"
        assert "Connection timeout" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_empty_articles(self, newsapi_provider, mock_http_client, mock_cache):
        """Test handling of empty article list."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [],
        }
        mock_http_client.get.return_value = mock_response

        result = await newsapi_provider.get_news("UNKNOWN")

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_max_articles_limit(self, newsapi_provider, mock_http_client, mock_cache):
        """Test that articles are limited to max_articles."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {
                    "title": f"Article {i}",
                    "source": {"name": "Source"},
                    "publishedAt": "2024-01-15T10:00:00Z",
                    "url": f"https://example.com/{i}",
                    "description": "Description",
                }
                for i in range(10)
            ],
        }
        mock_http_client.get.return_value = mock_response

        result = await newsapi_provider.get_news("AAPL", max_articles=3)

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_missing_source_name(self, newsapi_provider, mock_http_client, mock_cache):
        """Test handling of missing source name."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {
                    "title": "Article without source",
                    "source": {},  # Missing name
                    "publishedAt": "2024-01-15T10:00:00Z",
                    "url": "https://example.com/1",
                    "description": "Description",
                },
            ],
        }
        mock_http_client.get.return_value = mock_response

        result = await newsapi_provider.get_news("AAPL")

        assert len(result) == 1
        assert result[0].source == "Unknown"
