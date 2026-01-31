"""Mock fundamentals provider for testing and development."""

from domain.recommendation import FundamentalMetrics

# Mock fundamental data for test tickers
MOCK_FUNDAMENTALS = {
    "AAPL": FundamentalMetrics(
        pe_ratio=28.5,
        revenue_growth=0.08,
        profit_margin=0.25,
        debt_to_equity=1.8,
        market_cap=2_900_000_000_000,  # ~2.9T
    ),
    "MSFT": FundamentalMetrics(
        pe_ratio=35.2,
        revenue_growth=0.12,
        profit_margin=0.36,
        debt_to_equity=0.4,
        market_cap=2_800_000_000_000,  # ~2.8T
    ),
    "GOOGL": FundamentalMetrics(
        pe_ratio=24.8,
        revenue_growth=0.10,
        profit_margin=0.22,
        debt_to_equity=0.1,
        market_cap=1_800_000_000_000,  # ~1.8T
    ),
    "AMZN": FundamentalMetrics(
        pe_ratio=62.5,
        revenue_growth=0.11,
        profit_margin=0.06,
        debt_to_equity=0.8,
        market_cap=1_850_000_000_000,  # ~1.85T
    ),
    "NVDA": FundamentalMetrics(
        pe_ratio=65.0,
        revenue_growth=0.55,
        profit_margin=0.45,
        debt_to_equity=0.4,
        market_cap=1_200_000_000_000,  # ~1.2T
    ),
    "META": FundamentalMetrics(
        pe_ratio=22.5,
        revenue_growth=0.15,
        profit_margin=0.28,
        debt_to_equity=0.2,
        market_cap=1_000_000_000_000,  # ~1T
    ),
    "TSLA": FundamentalMetrics(
        pe_ratio=72.0,
        revenue_growth=0.18,
        profit_margin=0.11,
        debt_to_equity=0.1,
        market_cap=790_000_000_000,  # ~790B
    ),
    "JPM": FundamentalMetrics(
        pe_ratio=11.5,
        revenue_growth=0.06,
        profit_margin=0.32,
        debt_to_equity=1.2,
        market_cap=500_000_000_000,  # ~500B
    ),
    "V": FundamentalMetrics(
        pe_ratio=29.0,
        revenue_growth=0.09,
        profit_margin=0.52,
        debt_to_equity=0.5,
        market_cap=550_000_000_000,  # ~550B
    ),
    "JNJ": FundamentalMetrics(
        pe_ratio=15.2,
        revenue_growth=0.04,
        profit_margin=0.18,
        debt_to_equity=0.4,
        market_cap=385_000_000_000,  # ~385B
    ),
}


def _generate_default_fundamentals(ticker: str) -> FundamentalMetrics:
    """Generate default fundamentals for unknown tickers."""
    # Use ticker hash for deterministic but varied values
    ticker_hash = sum(ord(c) for c in ticker)

    return FundamentalMetrics(
        pe_ratio=15.0 + (ticker_hash % 30),
        revenue_growth=0.05 + (ticker_hash % 20) * 0.01,
        profit_margin=0.10 + (ticker_hash % 25) * 0.01,
        debt_to_equity=0.3 + (ticker_hash % 15) * 0.1,
        market_cap=50_000_000_000 + (ticker_hash % 100) * 10_000_000_000,
    )


class MockFundamentalsProvider:
    """Mock implementation of FundamentalsProvider for testing."""

    async def get_fundamentals(self, ticker: str) -> FundamentalMetrics:
        """Return mock fundamental metrics for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            FundamentalMetrics with mock data
        """
        ticker = ticker.upper()

        if ticker in MOCK_FUNDAMENTALS:
            return MOCK_FUNDAMENTALS[ticker]

        return _generate_default_fundamentals(ticker)
