"""Polygon.io market data provider implementation."""

import logging
from datetime import UTC, datetime, timedelta

from adapters.cache import CacheEntry, ProviderCache, make_cache_key
from adapters.http_client import RetryingHttpClient
from domain.providers import InvalidTickerError, PriceHistory, ProviderError
from domain.recommendation import CompanyInfo

logger = logging.getLogger(__name__)

POLYGON_BASE_URL = "https://api.polygon.io"
PROVIDER_NAME = "polygon"


class PolygonMarketDataProvider:
    """Market data provider using Polygon.io API."""

    def __init__(
        self,
        api_key: str,
        http_client: RetryingHttpClient,
        cache: ProviderCache,
        cache_ttl_seconds: int = 60,
    ):
        """Initialize the Polygon market data provider.

        Args:
            api_key: Polygon.io API key
            http_client: HTTP client for making requests
            cache: Provider cache for storing responses
            cache_ttl_seconds: Cache TTL in seconds
        """
        self.api_key = api_key
        self.http_client = http_client
        self.cache = cache
        self.cache_ttl_seconds = cache_ttl_seconds

    async def get_price_history(self, ticker: str, days: int = 200) -> PriceHistory:
        """Fetch historical price data from Polygon.io.

        Args:
            ticker: Stock ticker symbol
            days: Number of days of history to fetch

        Returns:
            PriceHistory with OHLCV data

        Raises:
            ProviderError: If data cannot be fetched
        """
        # Check cache first
        cache_key = make_cache_key(PROVIDER_NAME, "price_history", ticker, days=days)
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for {cache_key}")
            return self._deserialize_price_history(cached.data)

        # Calculate date range
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=days)

        # Format dates for API
        from_date = start_date.strftime("%Y-%m-%d")
        to_date = end_date.strftime("%Y-%m-%d")

        # Build API URL
        url = f"{POLYGON_BASE_URL}/v2/aggs/ticker/{ticker}/range/1/day/{from_date}/{to_date}"

        try:
            response = await self.http_client.get(
                url,
                params={"adjusted": "true", "sort": "asc", "apiKey": self.api_key},
            )
            data = response.json()

            if data.get("status") == "ERROR":
                raise ProviderError(
                    PROVIDER_NAME,
                    ticker,
                    data.get("error", "Unknown API error"),
                )

            results = data.get("results", [])
            if not results:
                raise InvalidTickerError(
                    ticker,
                    f"Ticker '{ticker}' not found or has no trading data",
                )

            # Parse results into PriceHistory
            dates = []
            opens = []
            highs = []
            lows = []
            closes = []
            volumes = []

            for bar in results:
                # Polygon returns timestamp in milliseconds
                timestamp_ms = bar.get("t", 0)
                date_str = datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC).strftime("%Y-%m-%d")

                dates.append(date_str)
                opens.append(float(bar.get("o", 0)))
                highs.append(float(bar.get("h", 0)))
                lows.append(float(bar.get("l", 0)))
                closes.append(float(bar.get("c", 0)))
                volumes.append(int(bar.get("v", 0)))

            price_history = PriceHistory(
                ticker=ticker,
                dates=dates,
                opens=opens,
                highs=highs,
                lows=lows,
                closes=closes,
                volumes=volumes,
            )

            # Cache the result
            now = datetime.now(UTC)
            self.cache.set(
                CacheEntry(
                    cache_key=cache_key,
                    provider=PROVIDER_NAME,
                    data=self._serialize_price_history(price_history),
                    ticker=ticker,
                    fetched_at=now,
                    expires_at=now + timedelta(seconds=self.cache_ttl_seconds),
                )
            )

            logger.info(f"Fetched {len(dates)} price bars for {ticker} from Polygon")
            return price_history

        except InvalidTickerError:
            raise
        except ProviderError:
            raise
        except Exception as e:
            logger.error(f"Polygon API error for {ticker}: {e}")
            raise ProviderError(PROVIDER_NAME, ticker, str(e)) from e

    def _serialize_price_history(self, ph: PriceHistory) -> dict:
        """Serialize PriceHistory for caching."""
        return {
            "ticker": ph.ticker,
            "dates": ph.dates,
            "opens": ph.opens,
            "highs": ph.highs,
            "lows": ph.lows,
            "closes": ph.closes,
            "volumes": ph.volumes,
        }

    def _deserialize_price_history(self, data: dict) -> PriceHistory:
        """Deserialize PriceHistory from cache."""
        return PriceHistory(
            ticker=data["ticker"],
            dates=data["dates"],
            opens=data["opens"],
            highs=data["highs"],
            lows=data["lows"],
            closes=data["closes"],
            volumes=data["volumes"],
        )

    async def get_company_info(self, ticker: str) -> CompanyInfo:
        """Fetch company information from Polygon.io.

        Args:
            ticker: Stock ticker symbol

        Returns:
            CompanyInfo with name, sector, industry, etc.
        """
        # Check cache first
        cache_key = make_cache_key(PROVIDER_NAME, "company_info", ticker)
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for {cache_key}")
            return self._deserialize_company_info(cached.data)

        url = f"{POLYGON_BASE_URL}/v3/reference/tickers/{ticker}"

        try:
            response = await self.http_client.get(
                url,
                params={"apiKey": self.api_key},
            )
            data = response.json()

            if data.get("status") != "OK":
                logger.warning(f"Polygon company info error for {ticker}: {data}")
                return CompanyInfo(name=ticker)

            results = data.get("results", {})

            company_info = CompanyInfo(
                name=results.get("name", ticker),
                sector=None,  # Polygon doesn't have sector directly
                industry=results.get("sic_description"),
                exchange=results.get("primary_exchange"),
                description=results.get("description"),
                website=results.get("homepage_url"),
            )

            # Cache the result (24 hour TTL for company info)
            now = datetime.now(UTC)
            self.cache.set(
                CacheEntry(
                    cache_key=cache_key,
                    provider=PROVIDER_NAME,
                    data=self._serialize_company_info(company_info),
                    ticker=ticker,
                    fetched_at=now,
                    expires_at=now + timedelta(seconds=86400),
                )
            )

            logger.info(f"Fetched company info for {ticker} from Polygon")
            return company_info

        except Exception as e:
            logger.warning(f"Failed to fetch company info for {ticker}: {e}")
            return CompanyInfo(name=ticker)

    def _serialize_company_info(self, ci: CompanyInfo) -> dict:
        """Serialize CompanyInfo for caching."""
        return {
            "name": ci.name,
            "sector": ci.sector,
            "industry": ci.industry,
            "exchange": ci.exchange,
            "description": ci.description,
            "website": ci.website,
        }

    def _deserialize_company_info(self, data: dict) -> CompanyInfo:
        """Deserialize CompanyInfo from cache."""
        return CompanyInfo(
            name=data.get("name", "Unknown"),
            sector=data.get("sector"),
            industry=data.get("industry"),
            exchange=data.get("exchange"),
            description=data.get("description"),
            website=data.get("website"),
        )
