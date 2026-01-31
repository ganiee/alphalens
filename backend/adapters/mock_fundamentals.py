"""Mock fundamentals provider for testing and development."""

from domain.recommendation import CompanyInfo, FundamentalMetrics

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
    "GOOG": FundamentalMetrics(  # Class C shares (same company as GOOGL)
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

# Mock company information for test tickers
MOCK_COMPANY_INFO = {
    "AAPL": CompanyInfo(
        name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics",
        exchange="NASDAQ",
    ),
    "MSFT": CompanyInfo(
        name="Microsoft Corporation",
        sector="Technology",
        industry="Software - Infrastructure",
        exchange="NASDAQ",
    ),
    "GOOGL": CompanyInfo(
        name="Alphabet Inc.",
        sector="Technology",
        industry="Internet Content & Information",
        exchange="NASDAQ",
    ),
    "GOOG": CompanyInfo(  # Class C shares (same company as GOOGL)
        name="Alphabet Inc.",
        sector="Technology",
        industry="Internet Content & Information",
        exchange="NASDAQ",
    ),
    "AMZN": CompanyInfo(
        name="Amazon.com, Inc.",
        sector="Consumer Cyclical",
        industry="Internet Retail",
        exchange="NASDAQ",
    ),
    "NVDA": CompanyInfo(
        name="NVIDIA Corporation",
        sector="Technology",
        industry="Semiconductors",
        exchange="NASDAQ",
    ),
    "META": CompanyInfo(
        name="Meta Platforms, Inc.",
        sector="Technology",
        industry="Internet Content & Information",
        exchange="NASDAQ",
    ),
    "TSLA": CompanyInfo(
        name="Tesla, Inc.",
        sector="Consumer Cyclical",
        industry="Auto Manufacturers",
        exchange="NASDAQ",
    ),
    "JPM": CompanyInfo(
        name="JPMorgan Chase & Co.",
        sector="Financial Services",
        industry="Banks - Diversified",
        exchange="NYSE",
    ),
    "V": CompanyInfo(
        name="Visa Inc.",
        sector="Financial Services",
        industry="Credit Services",
        exchange="NYSE",
    ),
    "JNJ": CompanyInfo(
        name="Johnson & Johnson",
        sector="Healthcare",
        industry="Drug Manufacturers - General",
        exchange="NYSE",
    ),
}


def _generate_default_company_info(ticker: str) -> CompanyInfo:
    """Generate default company info for unknown tickers."""
    return CompanyInfo(
        name=f"{ticker} Inc.",
        sector="Unknown",
        industry="Unknown",
        exchange="UNKNOWN",
    )


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

    async def get_company_info(self, ticker: str) -> CompanyInfo:
        """Return mock company information for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            CompanyInfo with mock data
        """
        ticker = ticker.upper()

        if ticker in MOCK_COMPANY_INFO:
            return MOCK_COMPANY_INFO[ticker]

        return _generate_default_company_info(ticker)
