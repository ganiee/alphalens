"""Tests for the Financial Modeling Prep fundamentals provider."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from adapters.cache import CacheEntry
from adapters.fmp_fundamentals import FMPFundamentalsProvider
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
def fmp_provider(mock_http_client, mock_cache):
    """Create an FMP provider with mocked dependencies."""
    return FMPFundamentalsProvider(
        api_key="test-api-key",
        http_client=mock_http_client,
        cache=mock_cache,
        cache_ttl_seconds=86400,
    )


class TestFMPFundamentalsProvider:
    """Tests for the FMPFundamentalsProvider."""

    @pytest.mark.asyncio
    async def test_successful_fetch(self, fmp_provider, mock_http_client, mock_cache):
        """Test successful fundamentals fetch combining multiple endpoints."""
        # Mock responses for each endpoint
        profile_response = MagicMock()
        profile_response.json.return_value = [
            {"mktCap": 3000000000000, "symbol": "AAPL"}
        ]

        ratios_response = MagicMock()
        ratios_response.json.return_value = [
            {
                "peRatioTTM": 28.5,
                "netProfitMarginTTM": 0.25,
                "debtEquityRatioTTM": 1.8,
            }
        ]

        metrics_response = MagicMock()
        metrics_response.json.return_value = [
            {"revenuePerShareTTM": 25.5}
        ]

        # Set up mock to return different responses based on URL
        async def mock_get(url, **kwargs):
            if "/profile/" in url:
                return profile_response
            elif "/ratios-ttm/" in url:
                return ratios_response
            elif "/key-metrics-ttm/" in url:
                return metrics_response
            raise ValueError(f"Unexpected URL: {url}")

        mock_http_client.get = AsyncMock(side_effect=mock_get)

        # Fetch data
        result = await fmp_provider.get_fundamentals("AAPL")

        # Verify result
        assert result.pe_ratio == 28.5
        assert result.profit_margin == 0.25
        assert result.debt_to_equity == 1.8
        assert result.market_cap == 3000000000000
        assert result.revenue_growth == 25.5

        # Verify cache was updated
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_cached_data(self, mock_http_client):
        """Test that cached data is returned without API call."""
        cache = MagicMock()
        cached_entry = CacheEntry(
            cache_key="fmp:fundamentals:AAPL",
            provider="fmp",
            data={
                "pe_ratio": 25.0,
                "revenue_growth": 0.15,
                "profit_margin": 0.22,
                "debt_to_equity": 1.5,
                "market_cap": 2500000000000,
            },
            ticker="AAPL",
            fetched_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
        cache.get.return_value = cached_entry

        provider = FMPFundamentalsProvider(
            api_key="test-key",
            http_client=mock_http_client,
            cache=cache,
        )

        result = await provider.get_fundamentals("AAPL")

        assert result.pe_ratio == 25.0
        assert result.market_cap == 2500000000000

        # Verify no HTTP call was made
        mock_http_client.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_null_values(self, fmp_provider, mock_http_client, mock_cache):
        """Test handling of null/missing values in API response."""
        profile_response = MagicMock()
        profile_response.json.return_value = [{"mktCap": None}]

        ratios_response = MagicMock()
        ratios_response.json.return_value = [
            {"peRatioTTM": None, "netProfitMarginTTM": 0.20, "debtEquityRatioTTM": None}
        ]

        metrics_response = MagicMock()
        metrics_response.json.return_value = [{}]  # Empty response

        async def mock_get(url, **kwargs):
            if "/profile/" in url:
                return profile_response
            elif "/ratios-ttm/" in url:
                return ratios_response
            elif "/key-metrics-ttm/" in url:
                return metrics_response
            raise ValueError(f"Unexpected URL: {url}")

        mock_http_client.get = AsyncMock(side_effect=mock_get)

        result = await fmp_provider.get_fundamentals("AAPL")

        assert result.pe_ratio is None
        assert result.profit_margin == 0.20
        assert result.debt_to_equity is None
        assert result.market_cap is None

    @pytest.mark.asyncio
    async def test_api_error_response(self, fmp_provider, mock_http_client):
        """Test handling of API error response."""
        error_response = MagicMock()
        error_response.json.return_value = {"Error Message": "Invalid API key"}

        mock_http_client.get.return_value = error_response

        with pytest.raises(ProviderError) as exc_info:
            await fmp_provider.get_fundamentals("AAPL")

        assert exc_info.value.provider == "fmp"
        assert "Invalid API key" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_http_error(self, fmp_provider, mock_http_client):
        """Test handling of HTTP errors."""
        mock_http_client.get.side_effect = httpx.HTTPError("Connection failed")

        with pytest.raises(ProviderError) as exc_info:
            await fmp_provider.get_fundamentals("AAPL")

        assert exc_info.value.provider == "fmp"
        assert "Connection failed" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_empty_response_list(self, fmp_provider, mock_http_client, mock_cache):
        """Test handling of empty response lists."""
        empty_response = MagicMock()
        empty_response.json.return_value = []

        mock_http_client.get.return_value = empty_response

        result = await fmp_provider.get_fundamentals("UNKNOWN")

        # Should return FundamentalMetrics with all None values
        assert result.pe_ratio is None
        assert result.market_cap is None

    @pytest.mark.asyncio
    async def test_cache_key_format(self, fmp_provider, mock_http_client, mock_cache):
        """Test that cache key is correctly formatted."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{}]
        mock_http_client.get.return_value = mock_response

        await fmp_provider.get_fundamentals("MSFT")

        # Check cache.get was called with correct key
        mock_cache.get.assert_called_once()
        call_args = mock_cache.get.call_args[0][0]
        assert "fmp" in call_args
        assert "fundamentals" in call_args
        assert "MSFT" in call_args
