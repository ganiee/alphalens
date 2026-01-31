"""Tests for technical indicator calculations."""


from domain.providers import PriceHistory
from services.indicators import (
    calculate_ema,
    calculate_macd,
    calculate_rsi,
    calculate_sma,
    calculate_volume_trend,
    compute_technical_indicators,
)


class TestSMA:
    """Tests for Simple Moving Average calculation."""

    def test_sma_basic(self):
        """Test basic SMA calculation."""
        prices = [10.0, 20.0, 30.0, 40.0, 50.0]
        assert calculate_sma(prices, 3) == 40.0  # (30 + 40 + 50) / 3

    def test_sma_insufficient_data(self):
        """Test SMA returns None with insufficient data."""
        prices = [10.0, 20.0]
        assert calculate_sma(prices, 5) is None

    def test_sma_exact_period(self):
        """Test SMA with exactly enough data."""
        prices = [10.0, 20.0, 30.0]
        assert calculate_sma(prices, 3) == 20.0


class TestEMA:
    """Tests for Exponential Moving Average calculation."""

    def test_ema_basic(self):
        """Test basic EMA calculation."""
        prices = [10.0, 12.0, 14.0, 16.0, 18.0, 20.0]
        ema = calculate_ema(prices, 3)
        assert ema is not None
        assert 16 < ema < 20  # EMA should be weighted toward recent prices

    def test_ema_insufficient_data(self):
        """Test EMA returns None with insufficient data."""
        prices = [10.0, 20.0]
        assert calculate_ema(prices, 5) is None


class TestRSI:
    """Tests for Relative Strength Index calculation."""

    def test_rsi_uptrend(self):
        """Test RSI in strong uptrend approaches 100."""
        # Consistently rising prices
        prices = [100 + i * 2 for i in range(20)]
        rsi = calculate_rsi(prices, 14)
        assert rsi > 70  # Should indicate overbought

    def test_rsi_downtrend(self):
        """Test RSI in strong downtrend approaches 0."""
        # Consistently falling prices
        prices = [100 - i * 2 for i in range(20)]
        rsi = calculate_rsi(prices, 14)
        assert rsi < 30  # Should indicate oversold

    def test_rsi_neutral(self):
        """Test RSI with mixed movement is around 50."""
        # Alternating up and down
        prices = [100 + (i % 2) * 2 for i in range(20)]
        rsi = calculate_rsi(prices, 14)
        assert 40 < rsi < 60  # Should be neutral

    def test_rsi_insufficient_data(self):
        """Test RSI returns default with insufficient data."""
        prices = [10.0, 12.0, 11.0]
        rsi = calculate_rsi(prices, 14)
        assert rsi == 50.0  # Default neutral

    def test_rsi_range(self):
        """Test RSI is always between 0 and 100."""
        prices = [100 + i for i in range(50)]
        rsi = calculate_rsi(prices, 14)
        assert 0 <= rsi <= 100


class TestMACD:
    """Tests for MACD calculation."""

    def test_macd_uptrend(self):
        """Test MACD is positive in uptrend."""
        # Rising prices
        prices = [100 + i * 0.5 for i in range(50)]
        macd, signal, histogram = calculate_macd(prices)
        assert macd > 0  # Fast EMA above slow EMA

    def test_macd_downtrend(self):
        """Test MACD is negative in downtrend."""
        # Falling prices
        prices = [100 - i * 0.5 for i in range(50)]
        macd, signal, histogram = calculate_macd(prices)
        assert macd < 0  # Fast EMA below slow EMA

    def test_macd_histogram(self):
        """Test MACD histogram is macd - signal."""
        prices = [100 + i for i in range(50)]
        macd, signal, histogram = calculate_macd(prices)
        assert abs(histogram - (macd - signal)) < 0.001

    def test_macd_insufficient_data(self):
        """Test MACD returns zeros with insufficient data."""
        prices = [10.0, 12.0, 14.0]
        macd, signal, histogram = calculate_macd(prices)
        assert macd == 0.0
        assert signal == 0.0
        assert histogram == 0.0


class TestVolumeTrend:
    """Tests for volume trend calculation."""

    def test_increasing_volume(self):
        """Test detection of increasing volume."""
        # Recent volume higher than historical
        volumes = [1000] * 30
        volumes[-10:] = [2000] * 10  # Recent spike
        trend = calculate_volume_trend(volumes)
        assert trend >= 1.5  # Significantly increasing

    def test_decreasing_volume(self):
        """Test detection of decreasing volume."""
        # Recent volume lower than historical
        volumes = [2000] * 30
        volumes[-10:] = [1000] * 10  # Recent decline
        trend = calculate_volume_trend(volumes)
        assert trend < 0.7  # Significantly decreasing

    def test_stable_volume(self):
        """Test stable volume around 1.0."""
        volumes = [1000] * 50
        trend = calculate_volume_trend(volumes)
        assert 0.9 < trend < 1.1  # Stable

    def test_insufficient_data(self):
        """Test returns 1.0 with insufficient data."""
        volumes = [1000] * 10
        trend = calculate_volume_trend(volumes, short_period=10, long_period=30)
        assert trend == 1.0


class TestComputeTechnicalIndicators:
    """Tests for full indicator computation."""

    def test_compute_all_indicators(self):
        """Test computation of all indicators from price history."""
        # Create mock price history
        dates = [f"2024-01-{i:02d}" for i in range(1, 201)]
        closes = [100 + i * 0.1 for i in range(200)]
        opens = [c - 0.5 for c in closes]
        highs = [c + 1 for c in closes]
        lows = [c - 1 for c in closes]
        volumes = [1000000] * 200

        price_history = PriceHistory(
            ticker="TEST",
            dates=dates,
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            volumes=volumes,
        )

        indicators = compute_technical_indicators(price_history)

        # Verify all fields are populated
        assert 0 <= indicators.rsi <= 100
        assert indicators.macd != 0 or indicators.macd_signal != 0
        assert indicators.sma_50 > 0
        assert indicators.sma_200 > 0
        assert indicators.current_price > 0
        assert indicators.volume_trend > 0

    def test_indicators_with_uptrend_data(self):
        """Test indicators show bullish signals in uptrend."""
        dates = [f"2024-01-{i:02d}" for i in range(1, 201)]
        # Strong uptrend
        closes = [100 + i for i in range(200)]
        opens = [c - 0.5 for c in closes]
        highs = [c + 1 for c in closes]
        lows = [c - 1 for c in closes]
        volumes = [1000000 + i * 1000 for i in range(200)]  # Increasing volume

        price_history = PriceHistory(
            ticker="TEST",
            dates=dates,
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            volumes=volumes,
        )

        indicators = compute_technical_indicators(price_history)

        # In uptrend: price should be above SMAs
        assert indicators.current_price > indicators.sma_50
        assert indicators.current_price > indicators.sma_200
