"""Mock market data provider for testing and development."""

import math
from datetime import datetime, timedelta

from domain.providers import PriceHistory

# Base prices for mock tickers (as of a fixed date)
MOCK_BASE_PRICES = {
    "AAPL": 185.0,
    "MSFT": 378.0,
    "GOOGL": 141.0,
    "AMZN": 178.0,
    "NVDA": 495.0,
    "META": 390.0,
    "TSLA": 248.0,
    "JPM": 172.0,
    "V": 275.0,
    "JNJ": 160.0,
}

# Default price for unknown tickers
DEFAULT_BASE_PRICE = 100.0


def _generate_price_series(
    base_price: float, days: int, volatility: float = 0.02, trend: float = 0.0001
) -> tuple[list[float], list[float], list[float], list[float], list[int]]:
    """Generate synthetic OHLCV price series.

    Args:
        base_price: Starting price
        days: Number of days to generate
        volatility: Daily volatility factor
        trend: Daily trend factor (positive = uptrend)

    Returns:
        Tuple of (opens, highs, lows, closes, volumes)
    """
    opens = []
    highs = []
    lows = []
    closes = []
    volumes = []

    price = base_price
    base_volume = 10_000_000

    for i in range(days):
        # Add some deterministic variation based on day index
        day_factor = math.sin(i * 0.1) * volatility + trend
        daily_change = 1 + day_factor

        open_price = price
        # Intraday movement
        high_price = open_price * (1 + abs(day_factor) * 0.5)
        low_price = open_price * (1 - abs(day_factor) * 0.5)
        close_price = price * daily_change

        opens.append(round(open_price, 2))
        highs.append(round(high_price, 2))
        lows.append(round(low_price, 2))
        closes.append(round(close_price, 2))

        # Volume varies with a pattern
        volume = int(base_volume * (1 + 0.3 * math.sin(i * 0.2)))
        volumes.append(volume)

        price = close_price

    return opens, highs, lows, closes, volumes


def _generate_dates(days: int) -> list[str]:
    """Generate list of date strings going back from today."""
    dates = []
    # Use a fixed reference date for deterministic tests
    end_date = datetime(2024, 1, 15)
    for i in range(days - 1, -1, -1):
        date = end_date - timedelta(days=i)
        # Skip weekends
        while date.weekday() >= 5:
            date -= timedelta(days=1)
        dates.append(date.strftime("%Y-%m-%d"))
    return dates


class MockMarketDataProvider:
    """Mock implementation of MarketDataProvider for testing."""

    def __init__(self) -> None:
        self._cache: dict[str, PriceHistory] = {}

    async def get_price_history(self, ticker: str, days: int = 200) -> PriceHistory:
        """Return mock price history for a ticker.

        Args:
            ticker: Stock ticker symbol
            days: Number of days of history

        Returns:
            PriceHistory with synthetic OHLCV data
        """
        ticker = ticker.upper()

        # Check cache
        cache_key = f"{ticker}_{days}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Get base price for ticker
        base_price = MOCK_BASE_PRICES.get(ticker, DEFAULT_BASE_PRICE)

        # Vary volatility and trend by ticker for diversity
        ticker_hash = sum(ord(c) for c in ticker)
        volatility = 0.015 + (ticker_hash % 10) * 0.002
        trend = 0.0001 if ticker_hash % 2 == 0 else -0.00005

        # Generate data
        dates = _generate_dates(days)
        opens, highs, lows, closes, volumes = _generate_price_series(
            base_price, days, volatility, trend
        )

        price_history = PriceHistory(
            ticker=ticker,
            dates=dates,
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            volumes=volumes,
        )

        self._cache[cache_key] = price_history
        return price_history
