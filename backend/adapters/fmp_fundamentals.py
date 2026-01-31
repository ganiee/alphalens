"""Financial Modeling Prep (FMP) fundamentals data provider implementation."""

import logging
from datetime import datetime, timedelta, timezone

from adapters.cache import CacheEntry, ProviderCache, make_cache_key
from adapters.http_client import RetryingHttpClient
from domain.providers import ProviderError
from domain.recommendation import FundamentalMetrics

logger = logging.getLogger(__name__)

FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"
PROVIDER_NAME = "fmp"


class FMPFundamentalsProvider:
    """Fundamentals data provider using Financial Modeling Prep API."""

    def __init__(
        self,
        api_key: str,
        http_client: RetryingHttpClient,
        cache: ProviderCache,
        cache_ttl_seconds: int = 86400,
    ):
        """Initialize the FMP fundamentals provider.

        Args:
            api_key: FMP API key
            http_client: HTTP client for making requests
            cache: Provider cache for storing responses
            cache_ttl_seconds: Cache TTL in seconds (default 24 hours)
        """
        self.api_key = api_key
        self.http_client = http_client
        self.cache = cache
        self.cache_ttl_seconds = cache_ttl_seconds

    async def get_fundamentals(self, ticker: str) -> FundamentalMetrics:
        """Fetch fundamental metrics from FMP.

        Combines data from profile, ratios-ttm, and key-metrics-ttm endpoints.

        Args:
            ticker: Stock ticker symbol

        Returns:
            FundamentalMetrics with PE, margins, growth, debt ratio, market cap

        Raises:
            ProviderError: If data cannot be fetched
        """
        # Check cache first
        cache_key = make_cache_key(PROVIDER_NAME, "fundamentals", ticker)
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for {cache_key}")
            return self._deserialize_fundamentals(cached.data)

        try:
            # Fetch profile data (contains market cap)
            profile_data = await self._fetch_endpoint(f"/profile/{ticker}")

            # Fetch TTM ratios (contains PE ratio)
            ratios_data = await self._fetch_endpoint(f"/ratios-ttm/{ticker}")

            # Fetch TTM key metrics (contains profit margin, etc.)
            metrics_data = await self._fetch_endpoint(f"/key-metrics-ttm/{ticker}")

            # Extract and combine metrics
            profile = profile_data[0] if profile_data else {}
            ratios = ratios_data[0] if ratios_data else {}
            metrics = metrics_data[0] if metrics_data else {}

            fundamentals = FundamentalMetrics(
                pe_ratio=self._safe_float(ratios.get("peRatioTTM")),
                revenue_growth=self._safe_float(metrics.get("revenuePerShareTTM")),
                profit_margin=self._safe_float(ratios.get("netProfitMarginTTM")),
                debt_to_equity=self._safe_float(ratios.get("debtEquityRatioTTM")),
                market_cap=self._safe_float(profile.get("mktCap")),
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

            logger.info(f"Fetched fundamentals for {ticker} from FMP")
            return fundamentals

        except ProviderError:
            raise
        except Exception as e:
            logger.error(f"FMP API error for {ticker}: {e}")
            raise ProviderError(PROVIDER_NAME, ticker, str(e))

    async def _fetch_endpoint(self, endpoint: str) -> list:
        """Fetch data from an FMP API endpoint.

        Args:
            endpoint: API endpoint path (e.g., "/profile/AAPL")

        Returns:
            Parsed JSON response (usually a list)

        Raises:
            ProviderError: If the request fails
        """
        url = f"{FMP_BASE_URL}{endpoint}"

        response = await self.http_client.get(
            url,
            params={"apikey": self.api_key},
        )

        data = response.json()

        # FMP returns error messages as objects
        if isinstance(data, dict) and "Error Message" in data:
            raise ProviderError(
                PROVIDER_NAME,
                endpoint,
                data["Error Message"],
            )

        return data if isinstance(data, list) else [data]

    def _safe_float(self, value) -> float | None:
        """Safely convert a value to float, returning None on failure."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _serialize_fundamentals(self, fm: FundamentalMetrics) -> dict:
        """Serialize FundamentalMetrics for caching."""
        return {
            "pe_ratio": fm.pe_ratio,
            "revenue_growth": fm.revenue_growth,
            "profit_margin": fm.profit_margin,
            "debt_to_equity": fm.debt_to_equity,
            "market_cap": fm.market_cap,
        }

    def _deserialize_fundamentals(self, data: dict) -> FundamentalMetrics:
        """Deserialize FundamentalMetrics from cache."""
        return FundamentalMetrics(
            pe_ratio=data.get("pe_ratio"),
            revenue_growth=data.get("revenue_growth"),
            profit_margin=data.get("profit_margin"),
            debt_to_equity=data.get("debt_to_equity"),
            market_cap=data.get("market_cap"),
        )
