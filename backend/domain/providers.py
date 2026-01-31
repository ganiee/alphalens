"""Port interfaces (protocols) for external data providers."""

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel

from domain.recommendation import (
    FundamentalMetrics,
    SentimentData,
)


class ProviderMetadata(BaseModel):
    """Metadata about a provider response."""

    provider: str
    fetched_at: datetime
    cached: bool = False


class PriceBar(Protocol):
    """Single price bar data."""

    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class PriceHistory:
    """Price history data for a stock."""

    def __init__(
        self,
        ticker: str,
        dates: list[str],
        opens: list[float],
        highs: list[float],
        lows: list[float],
        closes: list[float],
        volumes: list[int],
    ):
        self.ticker = ticker
        self.dates = dates
        self.opens = opens
        self.highs = highs
        self.lows = lows
        self.closes = closes
        self.volumes = volumes

    def __len__(self) -> int:
        return len(self.dates)

    @property
    def latest_close(self) -> float:
        """Get the most recent closing price."""
        return self.closes[-1] if self.closes else 0.0

    @property
    def latest_volume(self) -> int:
        """Get the most recent volume."""
        return self.volumes[-1] if self.volumes else 0


class MarketDataProvider(Protocol):
    """Protocol for fetching market price data."""

    async def get_price_history(self, ticker: str, days: int = 200) -> PriceHistory:
        """Fetch historical price data for a ticker.

        Args:
            ticker: Stock ticker symbol
            days: Number of days of history to fetch

        Returns:
            PriceHistory with OHLCV data

        Raises:
            ProviderError: If data cannot be fetched
        """
        ...


class FundamentalsProvider(Protocol):
    """Protocol for fetching fundamental financial data."""

    async def get_fundamentals(self, ticker: str) -> FundamentalMetrics:
        """Fetch fundamental metrics for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            FundamentalMetrics with P/E, margins, etc.

        Raises:
            ProviderError: If data cannot be fetched
        """
        ...


class NewsArticle:
    """A single news article."""

    def __init__(
        self,
        title: str,
        source: str,
        published_at: str,
        url: str,
        summary: str | None = None,
    ):
        self.title = title
        self.source = source
        self.published_at = published_at
        self.url = url
        self.summary = summary


class NewsProvider(Protocol):
    """Protocol for fetching news articles."""

    async def get_news(self, ticker: str, max_articles: int = 20) -> list[NewsArticle]:
        """Fetch recent news articles for a ticker.

        Args:
            ticker: Stock ticker symbol
            max_articles: Maximum number of articles to return

        Returns:
            List of NewsArticle objects

        Raises:
            ProviderError: If news cannot be fetched
        """
        ...


class SentimentAnalyzer(Protocol):
    """Protocol for analyzing text sentiment."""

    async def analyze_sentiment(self, ticker: str, articles: list[NewsArticle]) -> SentimentData:
        """Analyze sentiment from news articles.

        Args:
            ticker: Stock ticker symbol
            articles: List of news articles to analyze

        Returns:
            SentimentData with scores and counts

        Raises:
            ProviderError: If analysis fails
        """
        ...


class ProviderError(Exception):
    """Raised when a data provider fails."""

    def __init__(self, provider: str, ticker: str, message: str):
        self.provider = provider
        self.ticker = ticker
        self.message = message
        super().__init__(f"{provider} error for {ticker}: {message}")
