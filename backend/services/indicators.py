"""Technical indicator calculations."""

from domain.providers import PriceHistory
from domain.recommendation import TechnicalIndicators


def calculate_sma(prices: list[float], period: int) -> float | None:
    """Calculate Simple Moving Average.

    Args:
        prices: List of closing prices (oldest to newest)
        period: Number of periods for SMA

    Returns:
        SMA value or None if insufficient data
    """
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def calculate_ema(prices: list[float], period: int) -> float | None:
    """Calculate Exponential Moving Average.

    Args:
        prices: List of closing prices (oldest to newest)
        period: Number of periods for EMA

    Returns:
        EMA value or None if insufficient data
    """
    if len(prices) < period:
        return None

    multiplier = 2 / (period + 1)

    # Start with SMA for first EMA value
    ema = sum(prices[:period]) / period

    # Calculate EMA for remaining prices
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema

    return ema


def calculate_rsi(prices: list[float], period: int = 14) -> float:
    """Calculate Relative Strength Index.

    Args:
        prices: List of closing prices (oldest to newest)
        period: RSI period (default 14)

    Returns:
        RSI value between 0 and 100
    """
    if len(prices) < period + 1:
        return 50.0  # Default to neutral

    # Calculate price changes
    changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

    # Separate gains and losses
    gains = [max(0, change) for change in changes]
    losses = [abs(min(0, change)) for change in changes]

    # Calculate average gain and loss
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return round(rsi, 2)


def calculate_macd(
    prices: list[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> tuple[float, float, float]:
    """Calculate MACD (Moving Average Convergence Divergence).

    Args:
        prices: List of closing prices (oldest to newest)
        fast_period: Fast EMA period (default 12)
        slow_period: Slow EMA period (default 26)
        signal_period: Signal line period (default 9)

    Returns:
        Tuple of (MACD line, signal line, histogram)
    """
    if len(prices) < slow_period + signal_period:
        return (0.0, 0.0, 0.0)  # Default values

    fast_ema = calculate_ema(prices, fast_period)
    slow_ema = calculate_ema(prices, slow_period)

    if fast_ema is None or slow_ema is None:
        return (0.0, 0.0, 0.0)

    macd_line = fast_ema - slow_ema

    # Calculate MACD values for signal line calculation
    macd_values = []
    for i in range(slow_period, len(prices) + 1):
        subset = prices[:i]
        fast = calculate_ema(subset, fast_period)
        slow = calculate_ema(subset, slow_period)
        if fast is not None and slow is not None:
            macd_values.append(fast - slow)

    # Calculate signal line as EMA of MACD values
    if len(macd_values) >= signal_period:
        signal_line = calculate_ema(macd_values, signal_period)
        if signal_line is None:
            signal_line = 0.0
    else:
        signal_line = 0.0

    histogram = macd_line - signal_line

    return (round(macd_line, 4), round(signal_line, 4), round(histogram, 4))


def calculate_volume_trend(
    volumes: list[int], short_period: int = 10, long_period: int = 30
) -> float:
    """Calculate volume trend ratio.

    Args:
        volumes: List of trading volumes (oldest to newest)
        short_period: Short-term average period
        long_period: Long-term average period

    Returns:
        Ratio of short-term to long-term volume (>1 = increasing, <1 = decreasing)
    """
    if len(volumes) < long_period:
        return 1.0  # Neutral

    short_avg = sum(volumes[-short_period:]) / short_period
    long_avg = sum(volumes[-long_period:]) / long_period

    if long_avg == 0:
        return 1.0

    return round(short_avg / long_avg, 3)


def compute_technical_indicators(price_history: PriceHistory) -> TechnicalIndicators:
    """Compute all technical indicators from price history.

    Args:
        price_history: Historical OHLCV data

    Returns:
        TechnicalIndicators with all computed values
    """
    closes = price_history.closes
    volumes = price_history.volumes

    # Calculate indicators
    rsi = calculate_rsi(closes)
    macd, macd_signal, macd_histogram = calculate_macd(closes)
    sma_50 = calculate_sma(closes, 50) or closes[-1]
    sma_200 = calculate_sma(closes, 200) or closes[-1]
    volume_trend = calculate_volume_trend(volumes)
    current_price = closes[-1] if closes else 0.0

    return TechnicalIndicators(
        rsi=rsi,
        macd=macd,
        macd_signal=macd_signal,
        macd_histogram=macd_histogram,
        sma_50=round(sma_50, 2),
        sma_200=round(sma_200, 2),
        current_price=round(current_price, 2),
        volume_trend=volume_trend,
    )
