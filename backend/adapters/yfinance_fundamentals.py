"""Yahoo Finance fundamentals data provider using yfinance library."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import yfinance as yf

from adapters.cache import CacheEntry, ProviderCache, make_cache_key
from domain.providers import InvalidTickerError, ProviderError
from domain.recommendation import FundamentalMetrics

logger = logging.getLogger(__name__)

PROVIDER_NAME = "yfinance"


class YFinanceFundamentalsProvider:
    """Fundamentals data provider using Yahoo Finance (yfinance library)."""

    def __init__(
        self,
        cache: ProviderCache,
        cache_ttl_seconds: int = 86400,
    ):
        """Initialize the yfinance fundamentals provider.

        Args:
            cache: Provider cache for storing responses
            cache_ttl_seconds: Cache TTL in seconds (default 24 hours)
        """
        self.cache = cache
        self.cache_ttl_seconds = cache_ttl_seconds

    async def get_fundamentals(self, ticker: str) -> FundamentalMetrics:
        """Fetch fundamental metrics from Yahoo Finance.

        Args:
            ticker: Stock ticker symbol

        Returns:
            FundamentalMetrics with PE, margins, growth, debt ratio, market cap

        Raises:
            InvalidTickerError: If ticker doesn't exist
            ProviderError: If data cannot be fetched
        """
        # Check cache first
        cache_key = make_cache_key(PROVIDER_NAME, "fundamentals", ticker)
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for {cache_key}")
            return self._deserialize_fundamentals(cached.data)

        try:
            # Run yfinance in thread pool since it's synchronous
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, self._fetch_ticker_info, ticker)

            if not info or info.get("regularMarketPrice") is None:
                raise InvalidTickerError(ticker, f"No data found for ticker {ticker}")

            fundamentals = FundamentalMetrics(
                pe_ratio=self._safe_float(info.get("trailingPE")),
                revenue_growth=self._safe_float(info.get("revenueGrowth")),
                profit_margin=self._safe_float(info.get("profitMargins")),
                debt_to_equity=self._safe_float(info.get("debtToEquity"), divisor=100),
                market_cap=self._safe_int(info.get("marketCap")),
            )

            # Cache the result
            now = datetime.now(timezone.utc)
            self.cache.set(
                CacheEntry(
                    cache_key=cache_key,
                    provider=PROVIDER_NAME,
                    data=self._serialize_fundamentals(fundamentals),
                    ticker=ticker,
                    fetched_at=now,
                    expires_at=now + timedelta(seconds=self.cache_ttl_seconds),
                )
            )

            logger.info(f"Fetched fundamentals for {ticker} from yfinance")
            return fundamentals

        except InvalidTickerError:
            raise
        except Exception as e:
            logger.error(f"yfinance error for {ticker}: {e}")
            raise ProviderError(PROVIDER_NAME, ticker, str(e))

    def _fetch_ticker_info(self, ticker: str) -> dict:
        """Fetch ticker info synchronously (called in thread pool)."""
        stock = yf.Ticker(ticker)
        return stock.info

    def _safe_float(
        self, value, default: float | None = None, divisor: float = 1.0
    ) -> float | None:
        """Safely convert value to float."""
        if value is None:
            return default
        try:
            return float(value) / divisor
        except (ValueError, TypeError):
            return default

    def _safe_int(self, value, default: int | None = None) -> int | None:
        """Safely convert value to int."""
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _serialize_fundamentals(self, fundamentals: FundamentalMetrics) -> dict:
        """Serialize fundamentals for caching."""
        return {
            "pe_ratio": fundamentals.pe_ratio,
            "revenue_growth": fundamentals.revenue_growth,
            "profit_margin": fundamentals.profit_margin,
            "debt_to_equity": fundamentals.debt_to_equity,
            "market_cap": fundamentals.market_cap,
        }

    def _deserialize_fundamentals(self, data: dict) -> FundamentalMetrics:
        """Deserialize fundamentals from cache."""
        return FundamentalMetrics(
            pe_ratio=data.get("pe_ratio"),
            revenue_growth=data.get("revenue_growth"),
            profit_margin=data.get("profit_margin"),
            debt_to_equity=data.get("debt_to_equity"),
            market_cap=data.get("market_cap"),
        )
