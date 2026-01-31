"""Tests for scoring algorithms."""


from domain.recommendation import (
    FundamentalMetrics,
    ScoreBreakdown,
    SentimentData,
    TechnicalIndicators,
)
from services.scoring import (
    FUNDAMENTAL_WEIGHT,
    SENTIMENT_WEIGHT,
    TECHNICAL_WEIGHT,
    calculate_composite_score,
    calculate_fundamental_score,
    calculate_sentiment_score,
    calculate_technical_score,
    rank_and_allocate,
)


class TestTechnicalScore:
    """Tests for technical score calculation."""

    def test_score_range(self):
        """Test technical score is between 0 and 100."""
        indicators = TechnicalIndicators(
            rsi=50,
            macd=0.5,
            macd_signal=0.3,
            macd_histogram=0.2,
            sma_50=100,
            sma_200=95,
            current_price=105,
            volume_trend=1.1,
        )
        score = calculate_technical_score(indicators)
        assert 0 <= score <= 100

    def test_bullish_indicators_high_score(self):
        """Test bullish indicators produce high score."""
        indicators = TechnicalIndicators(
            rsi=25,  # Oversold - bullish
            macd=1.0,
            macd_signal=0.5,
            macd_histogram=0.5,  # Positive - bullish
            sma_50=100,
            sma_200=95,
            current_price=110,  # Above both SMAs - bullish
            volume_trend=1.3,  # Increasing volume - bullish
        )
        score = calculate_technical_score(indicators)
        assert score >= 70  # Should be high

    def test_bearish_indicators_low_score(self):
        """Test bearish indicators produce low score."""
        indicators = TechnicalIndicators(
            rsi=75,  # Overbought - bearish
            macd=-1.0,
            macd_signal=-0.5,
            macd_histogram=-0.5,  # Negative - bearish
            sma_50=100,
            sma_200=105,
            current_price=90,  # Below both SMAs - bearish
            volume_trend=0.7,  # Decreasing volume
        )
        score = calculate_technical_score(indicators)
        assert score <= 40  # Should be low


class TestFundamentalScore:
    """Tests for fundamental score calculation."""

    def test_score_range(self):
        """Test fundamental score is between 0 and 100."""
        metrics = FundamentalMetrics(
            pe_ratio=20,
            revenue_growth=0.10,
            profit_margin=0.15,
            debt_to_equity=0.5,
        )
        score = calculate_fundamental_score(metrics)
        assert 0 <= score <= 100

    def test_strong_fundamentals_high_score(self):
        """Test strong fundamentals produce high score."""
        metrics = FundamentalMetrics(
            pe_ratio=12,  # Undervalued
            revenue_growth=0.25,  # High growth
            profit_margin=0.30,  # Excellent margins
            debt_to_equity=0.2,  # Low debt
        )
        score = calculate_fundamental_score(metrics)
        assert score >= 80  # Should be high

    def test_weak_fundamentals_low_score(self):
        """Test weak fundamentals produce low score."""
        metrics = FundamentalMetrics(
            pe_ratio=60,  # Overvalued
            revenue_growth=-0.05,  # Declining
            profit_margin=0.02,  # Low margins
            debt_to_equity=3.0,  # High debt
        )
        score = calculate_fundamental_score(metrics)
        assert score <= 30  # Should be low

    def test_partial_data(self):
        """Test scoring with partial fundamental data."""
        metrics = FundamentalMetrics(
            pe_ratio=20,
            revenue_growth=None,  # Missing
            profit_margin=0.15,
            debt_to_equity=None,  # Missing
        )
        score = calculate_fundamental_score(metrics)
        assert 0 <= score <= 100  # Should still work


class TestSentimentScore:
    """Tests for sentiment score calculation."""

    def test_score_range(self):
        """Test sentiment score is between 0 and 100."""
        sentiment = SentimentData(
            score=0.0,  # Neutral
            article_count=15,
            positive_count=5,
            negative_count=5,
            neutral_count=5,
        )
        score = calculate_sentiment_score(sentiment)
        assert 0 <= score <= 100

    def test_positive_sentiment_high_score(self):
        """Test positive sentiment produces high score."""
        sentiment = SentimentData(
            score=0.8,  # Very positive
            article_count=20,
            positive_count=16,
            negative_count=2,
            neutral_count=2,
        )
        score = calculate_sentiment_score(sentiment)
        assert score >= 80  # Should be high

    def test_negative_sentiment_low_score(self):
        """Test negative sentiment produces low score."""
        sentiment = SentimentData(
            score=-0.8,  # Very negative
            article_count=20,
            positive_count=2,
            negative_count=16,
            neutral_count=2,
        )
        score = calculate_sentiment_score(sentiment)
        assert score <= 20  # Should be low

    def test_low_article_count_regression(self):
        """Test low article count regresses toward neutral."""
        # Same positive score but low article count
        sentiment = SentimentData(
            score=0.8,
            article_count=3,  # Very few articles
            positive_count=3,
            negative_count=0,
            neutral_count=0,
        )
        score = calculate_sentiment_score(sentiment)
        # Should be less extreme due to low confidence
        assert 50 < score < 80


class TestCompositeScore:
    """Tests for composite score calculation."""

    def test_weights_sum_to_one(self):
        """Test scoring weights sum to 1.0."""
        assert TECHNICAL_WEIGHT + FUNDAMENTAL_WEIGHT + SENTIMENT_WEIGHT == 1.0

    def test_composite_formula(self):
        """Test composite score follows the formula."""
        breakdown = ScoreBreakdown(
            technical=80,
            fundamental=60,
            sentiment=70,
        )
        expected = 80 * 0.4 + 60 * 0.3 + 70 * 0.3
        actual = calculate_composite_score(breakdown)
        assert abs(actual - expected) < 0.01

    def test_composite_range(self):
        """Test composite score is between 0 and 100."""
        breakdown = ScoreBreakdown(
            technical=50,
            fundamental=50,
            sentiment=50,
        )
        score = calculate_composite_score(breakdown)
        assert 0 <= score <= 100

    def test_all_high_scores(self):
        """Test all high component scores give high composite."""
        breakdown = ScoreBreakdown(
            technical=100,
            fundamental=100,
            sentiment=100,
        )
        score = calculate_composite_score(breakdown)
        assert score == 100.0

    def test_all_low_scores(self):
        """Test all low component scores give low composite."""
        breakdown = ScoreBreakdown(
            technical=0,
            fundamental=0,
            sentiment=0,
        )
        score = calculate_composite_score(breakdown)
        assert score == 0.0


class TestRankAndAllocate:
    """Tests for ranking and allocation."""

    def test_ranking_order(self):
        """Test stocks are ranked by composite score (highest first)."""
        scores = [
            ("AAPL", ScoreBreakdown(technical=60, fundamental=60, sentiment=60)),
            ("MSFT", ScoreBreakdown(technical=80, fundamental=80, sentiment=80)),
            ("GOOGL", ScoreBreakdown(technical=70, fundamental=70, sentiment=70)),
        ]
        results = rank_and_allocate(scores)

        assert results[0].ticker == "MSFT"  # Highest
        assert results[1].ticker == "GOOGL"  # Middle
        assert results[2].ticker == "AAPL"  # Lowest

        assert results[0].rank == 1
        assert results[1].rank == 2
        assert results[2].rank == 3

    def test_allocations_sum_to_100(self):
        """Test allocations sum to approximately 100%."""
        scores = [
            ("AAPL", ScoreBreakdown(technical=70, fundamental=65, sentiment=75)),
            ("MSFT", ScoreBreakdown(technical=80, fundamental=75, sentiment=80)),
            ("GOOGL", ScoreBreakdown(technical=60, fundamental=70, sentiment=65)),
        ]
        results = rank_and_allocate(scores)

        total = sum(r.allocation_pct for r in results)
        assert abs(total - 100.0) < 0.1  # Allow small rounding error

    def test_higher_score_higher_allocation(self):
        """Test higher scored stocks get higher allocation."""
        scores = [
            ("LOW", ScoreBreakdown(technical=30, fundamental=30, sentiment=30)),
            ("HIGH", ScoreBreakdown(technical=90, fundamental=90, sentiment=90)),
        ]
        results = rank_and_allocate(scores)

        high_result = next(r for r in results if r.ticker == "HIGH")
        low_result = next(r for r in results if r.ticker == "LOW")

        assert high_result.allocation_pct > low_result.allocation_pct

    def test_single_stock(self):
        """Test allocation with single stock gives 100%."""
        scores = [
            ("ONLY", ScoreBreakdown(technical=70, fundamental=70, sentiment=70)),
        ]
        results = rank_and_allocate(scores)

        assert len(results) == 1
        assert results[0].allocation_pct == 100.0
        assert results[0].rank == 1
