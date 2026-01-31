"""Tests for the Polygon.io market data provider."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from adapters.cache import CacheEntry, NoOpCache
from adapters.polygon_market_data import PolygonMarketDataProvider
from domain.providers import InvalidTickerError, ProviderError


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
def polygon_provider(mock_http_client, mock_cache):
    """Create a Polygon provider with mocked dependencies."""
    return PolygonMarketDataProvider(
        api_key="test-api-key",
        http_client=mock_http_client,
        cache=mock_cache,
        cache_ttl_seconds=60,
    )


class TestPolygonMarketDataProvider:
    """Tests for the PolygonMarketDataProvider."""

    @pytest.mark.asyncio
    async def test_successful_fetch(self, polygon_provider, mock_http_client, mock_cache):
        """Test successful price history fetch."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "OK",
            "results": [
                {"t": 1704067200000, "o": 100.0, "h": 102.0, "l": 99.0, "c": 101.0, "v": 1000000},
                {"t": 1704153600000, "o": 101.0, "h": 103.0, "l": 100.0, "c": 102.0, "v": 1100000},
            ],
        }
        mock_http_client.get.return_value = mock_response

        # Fetch data
        result = await polygon_provider.get_price_history("AAPL", days=200)

        # Verify result
        assert result.ticker == "AAPL"
        assert len(result.closes) == 2
        assert result.closes == [101.0, 102.0]
        assert result.volumes == [1000000, 1100000]
        assert result.latest_close == 102.0

        # Verify HTTP call
        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert "AAPL" in call_args[0][0]
        assert call_args[1]["params"]["apiKey"] == "test-api-key"

        # Verify cache was updated
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_cached_data(self, mock_http_client):
        """Test that cached data is returned without API call."""
        # Set up cache with data
        cache = MagicMock()
        cached_entry = CacheEntry(
            cache_key="polygon:price_history:AAPL:days=200",
            provider="polygon",
            data={
                "ticker": "AAPL",
                "dates": ["2024-01-01", "2024-01-02"],
                "opens": [100.0, 101.0],
                "highs": [102.0, 103.0],
                "lows": [99.0, 100.0],
                "closes": [101.0, 102.0],
                "volumes": [1000000, 1100000],
            },
            ticker="AAPL",
            fetched_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        cache.get.return_value = cached_entry

        provider = PolygonMarketDataProvider(
            api_key="test-key",
            http_client=mock_http_client,
            cache=cache,
        )

        # Fetch data
        result = await provider.get_price_history("AAPL", days=200)

        # Verify cached data was used
        assert result.ticker == "AAPL"
        assert result.closes == [101.0, 102.0]

        # Verify no HTTP call was made
        mock_http_client.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_api_error_response(self, polygon_provider, mock_http_client):
        """Test handling of API error response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ERROR",
            "error": "Invalid API key",
        }
        mock_http_client.get.return_value = mock_response

        with pytest.raises(ProviderError) as exc_info:
            await polygon_provider.get_price_history("AAPL")

        assert exc_info.value.provider == "polygon"
        assert exc_info.value.ticker == "AAPL"
        assert "Invalid API key" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_empty_results_raises_invalid_ticker(self, polygon_provider, mock_http_client):
        """Test that empty results raises InvalidTickerError."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "OK",
            "results": [],
        }
        mock_http_client.get.return_value = mock_response

        with pytest.raises(InvalidTickerError) as exc_info:
            await polygon_provider.get_price_history("INVALID")

        assert "INVALID" in exc_info.value.message
        assert "not found" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_http_error(self, polygon_provider, mock_http_client):
        """Test handling of HTTP errors."""
        mock_http_client.get.side_effect = httpx.HTTPError("Connection failed")

        with pytest.raises(ProviderError) as exc_info:
            await polygon_provider.get_price_history("AAPL")

        assert exc_info.value.provider == "polygon"
        assert "Connection failed" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_price_history_properties(self, polygon_provider, mock_http_client, mock_cache):
        """Test that PriceHistory has correct properties."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "OK",
            "results": [
                {"t": 1704067200000, "o": 100.0, "h": 105.0, "l": 98.0, "c": 103.0, "v": 500000},
                {"t": 1704153600000, "o": 103.0, "h": 107.0, "l": 102.0, "c": 106.0, "v": 600000},
                {"t": 1704240000000, "o": 106.0, "h": 108.0, "l": 104.0, "c": 107.5, "v": 550000},
            ],
        }
        mock_http_client.get.return_value = mock_response

        result = await polygon_provider.get_price_history("AAPL", days=30)

        assert len(result) == 3
        assert result.latest_close == 107.5
        assert result.latest_volume == 550000
        assert result.opens == [100.0, 103.0, 106.0]
        assert result.highs == [105.0, 107.0, 108.0]
        assert result.lows == [98.0, 102.0, 104.0]
