"""Tests for the Yahoo Finance fundamentals provider."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from adapters.cache import CacheEntry
from adapters.yfinance_fundamentals import YFinanceFundamentalsProvider
from domain.providers import InvalidTickerError, ProviderError


@pytest.fixture
def mock_cache():
    """Create a mock cache that returns None (cache miss)."""
    cache = MagicMock()
    cache.get.return_value = None
    return cache


@pytest.fixture
def yfinance_provider(mock_cache):
    """Create a yfinance provider with mocked cache."""
    return YFinanceFundamentalsProvider(
        cache=mock_cache,
        cache_ttl_seconds=86400,
    )


class TestYFinanceFundamentalsProvider:
    """Tests for the YFinanceFundamentalsProvider."""

    @pytest.mark.asyncio
    async def test_successful_fetch(self, yfinance_provider, mock_cache):
        """Test successful fundamentals fetch."""
        mock_info = {
            "regularMarketPrice": 150.0,
            "trailingPE": 25.5,
            "revenueGrowth": 0.12,
            "profitMargins": 0.25,
            "debtToEquity": 150.0,  # yfinance returns as percentage
            "marketCap": 2500000000000,
        }

        with patch.object(
            yfinance_provider, "_fetch_ticker_info", return_value=mock_info
        ):
            result = await yfinance_provider.get_fundamentals("AAPL")

        assert result.pe_ratio == 25.5
        assert result.revenue_growth == 0.12
        assert result.profit_margin == 0.25
        assert result.debt_to_equity == 1.5  # Divided by 100
        assert result.market_cap == 2500000000000

        # Verify cache was updated
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_cached_data(self):
        """Test that cached data is returned without API call."""
        cache = MagicMock()
        cached_entry = CacheEntry(
            cache_key="yfinance:fundamentals:AAPL",
            provider="yfinance",
            data={
                "pe_ratio": 28.0,
                "revenue_growth": 0.10,
                "profit_margin": 0.22,
                "debt_to_equity": 1.2,
                "market_cap": 2800000000000,
            },
            ticker="AAPL",
            fetched_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
        cache.get.return_value = cached_entry

        provider = YFinanceFundamentalsProvider(cache=cache)

        with patch.object(provider, "_fetch_ticker_info") as mock_fetch:
            result = await provider.get_fundamentals("AAPL")

        assert result.pe_ratio == 28.0
        assert result.market_cap == 2800000000000
        mock_fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_ticker(self, yfinance_provider):
        """Test handling of invalid ticker."""
        mock_info = {"regularMarketPrice": None}

        with patch.object(
            yfinance_provider, "_fetch_ticker_info", return_value=mock_info
        ), pytest.raises(InvalidTickerError) as exc_info:
            await yfinance_provider.get_fundamentals("INVALIDTICKER")

        assert "INVALIDTICKER" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_empty_info(self, yfinance_provider):
        """Test handling of empty info response."""
        with (
            patch.object(yfinance_provider, "_fetch_ticker_info", return_value={}),
            pytest.raises(InvalidTickerError),
        ):
            await yfinance_provider.get_fundamentals("BADTICKER")

    @pytest.mark.asyncio
    async def test_handles_null_values(self, yfinance_provider, mock_cache):
        """Test handling of null values in response."""
        mock_info = {
            "regularMarketPrice": 100.0,
            "trailingPE": None,
            "revenueGrowth": None,
            "profitMargins": 0.15,
            "debtToEquity": None,
            "marketCap": 500000000000,
        }

        with patch.object(
            yfinance_provider, "_fetch_ticker_info", return_value=mock_info
        ):
            result = await yfinance_provider.get_fundamentals("TEST")

        assert result.pe_ratio is None
        assert result.revenue_growth is None
        assert result.profit_margin == 0.15
        assert result.debt_to_equity is None
        assert result.market_cap == 500000000000

    @pytest.mark.asyncio
    async def test_exception_handling(self, yfinance_provider):
        """Test handling of exceptions."""
        with patch.object(
            yfinance_provider,
            "_fetch_ticker_info",
            side_effect=Exception("Network error"),
        ), pytest.raises(ProviderError) as exc_info:
            await yfinance_provider.get_fundamentals("AAPL")

        assert exc_info.value.provider == "yfinance"
        assert "Network error" in exc_info.value.message
