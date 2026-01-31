"""Tests for the recommendation service."""

import pytest

from adapters.mock_fundamentals import MockFundamentalsProvider
from adapters.mock_market_data import MockMarketDataProvider
from adapters.mock_news import MockNewsProvider
from adapters.mock_sentiment import MockSentimentAnalyzer
from domain.auth import User, UserPlan, UserRole
from domain.recommendation import (
    Horizon,
    PlanConstraintError,
    RecommendationRequest,
)
from services.recommendation import RecommendationService


@pytest.fixture
def recommendation_service():
    """Create a recommendation service with mock providers."""
    return RecommendationService(
        market_data=MockMarketDataProvider(),
        fundamentals=MockFundamentalsProvider(),
        news=MockNewsProvider(),
        sentiment=MockSentimentAnalyzer(),
    )


@pytest.fixture
def free_user():
    """Create a free tier user."""
    return User(
        sub="user-123",
        email="free@example.com",
        email_verified=True,
        roles=[UserRole.USER],
        plan=UserPlan.FREE,
    )


@pytest.fixture
def pro_user():
    """Create a pro tier user."""
    return User(
        sub="user-456",
        email="pro@example.com",
        email_verified=True,
        roles=[UserRole.USER],
        plan=UserPlan.PRO,
    )


class TestRecommendationService:
    """Tests for the RecommendationService."""

    @pytest.mark.asyncio
    async def test_run_returns_result(self, recommendation_service, free_user):
        """Test that run returns a RecommendationResult."""
        request = RecommendationRequest(
            tickers=["AAPL", "MSFT"],
            horizon=Horizon.ONE_MONTH,
        )

        result = await recommendation_service.run(request, free_user)

        assert result is not None
        assert result.run_id is not None
        assert result.user_id == free_user.sub

    @pytest.mark.asyncio
    async def test_result_has_scores_for_all_tickers(self, recommendation_service, free_user):
        """Test that result includes scores for all requested tickers."""
        request = RecommendationRequest(
            tickers=["AAPL", "MSFT", "GOOGL"],
            horizon=Horizon.ONE_MONTH,
        )

        result = await recommendation_service.run(request, free_user)

        assert len(result.scores) == 3
        tickers_in_result = {s.ticker for s in result.scores}
        assert tickers_in_result == {"AAPL", "MSFT", "GOOGL"}

    @pytest.mark.asyncio
    async def test_result_has_evidence_packets(self, recommendation_service, free_user):
        """Test that result includes evidence for all tickers."""
        request = RecommendationRequest(
            tickers=["AAPL", "MSFT"],
            horizon=Horizon.ONE_MONTH,
        )

        result = await recommendation_service.run(request, free_user)

        assert len(result.evidence) == 2
        for evidence in result.evidence:
            assert evidence.technical is not None
            assert evidence.fundamental is not None
            assert evidence.sentiment is not None

    @pytest.mark.asyncio
    async def test_stocks_ranked_by_score(self, recommendation_service, free_user):
        """Test that stocks are ranked highest score first."""
        request = RecommendationRequest(
            tickers=["AAPL", "MSFT", "GOOGL"],
            horizon=Horizon.ONE_MONTH,
        )

        result = await recommendation_service.run(request, free_user)

        # Verify ranks are sequential
        ranks = [s.rank for s in result.scores]
        assert ranks == [1, 2, 3]

        # Verify scores are in descending order
        scores = [s.composite_score for s in result.scores]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_allocations_sum_to_100(self, recommendation_service, free_user):
        """Test that allocations sum to approximately 100%."""
        request = RecommendationRequest(
            tickers=["AAPL", "MSFT"],
            horizon=Horizon.ONE_MONTH,
        )

        result = await recommendation_service.run(request, free_user)

        total = result.total_allocation
        assert abs(total - 100.0) < 0.1

    @pytest.mark.asyncio
    async def test_horizon_preserved(self, recommendation_service, pro_user):
        """Test that requested horizon is preserved in result."""
        request = RecommendationRequest(
            tickers=["AAPL"],
            horizon=Horizon.THREE_MONTHS,
        )

        result = await recommendation_service.run(request, pro_user)

        assert result.horizon == Horizon.THREE_MONTHS


class TestPlanConstraints:
    """Tests for plan constraint enforcement."""

    @pytest.mark.asyncio
    async def test_free_plan_max_3_tickers(self, recommendation_service, free_user):
        """Test free plan rejects more than 3 tickers."""
        request = RecommendationRequest(
            tickers=["AAPL", "MSFT", "GOOGL", "AMZN"],  # 4 tickers
            horizon=Horizon.ONE_MONTH,
        )

        with pytest.raises(PlanConstraintError) as exc_info:
            await recommendation_service.run(request, free_user)

        assert "3" in str(exc_info.value.message)
        assert "4" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_free_plan_allows_3_tickers(self, recommendation_service, free_user):
        """Test free plan allows exactly 3 tickers."""
        request = RecommendationRequest(
            tickers=["AAPL", "MSFT", "GOOGL"],  # 3 tickers
            horizon=Horizon.ONE_MONTH,
        )

        result = await recommendation_service.run(request, free_user)
        assert len(result.scores) == 3

    @pytest.mark.asyncio
    async def test_pro_plan_max_5_tickers(self, recommendation_service, pro_user):
        """Test pro plan allows up to 5 tickers."""
        request = RecommendationRequest(
            tickers=["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],  # 5 tickers
            horizon=Horizon.ONE_MONTH,
        )

        result = await recommendation_service.run(request, pro_user)
        assert len(result.scores) == 5

    @pytest.mark.asyncio
    async def test_pro_plan_rejects_6_tickers(self, recommendation_service, pro_user):
        """Test pro plan rejects more than 5 tickers."""
        request = RecommendationRequest(
            tickers=["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META"],  # 6 tickers
            horizon=Horizon.ONE_MONTH,
        )

        with pytest.raises(PlanConstraintError):
            await recommendation_service.run(request, pro_user)

    @pytest.mark.asyncio
    async def test_free_plan_1m_horizon_only(self, recommendation_service, free_user):
        """Test free plan only allows 1M horizon."""
        request = RecommendationRequest(
            tickers=["AAPL"],
            horizon=Horizon.THREE_MONTHS,  # Not allowed for free
        )

        with pytest.raises(PlanConstraintError) as exc_info:
            await recommendation_service.run(request, free_user)

        assert "horizon" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_free_plan_allows_1m(self, recommendation_service, free_user):
        """Test free plan allows 1M horizon."""
        request = RecommendationRequest(
            tickers=["AAPL"],
            horizon=Horizon.ONE_MONTH,
        )

        result = await recommendation_service.run(request, free_user)
        assert result.horizon == Horizon.ONE_MONTH

    @pytest.mark.asyncio
    async def test_pro_plan_all_horizons(self, recommendation_service, pro_user):
        """Test pro plan allows all horizons."""
        horizons = [
            Horizon.ONE_WEEK,
            Horizon.ONE_MONTH,
            Horizon.THREE_MONTHS,
            Horizon.SIX_MONTHS,
            Horizon.ONE_YEAR,
        ]

        for horizon in horizons:
            request = RecommendationRequest(
                tickers=["AAPL"],
                horizon=horizon,
            )
            result = await recommendation_service.run(request, pro_user)
            assert result.horizon == horizon


class TestEvidencePacket:
    """Tests for evidence packet content."""

    @pytest.mark.asyncio
    async def test_evidence_has_technical_indicators(self, recommendation_service, free_user):
        """Test evidence includes technical indicators."""
        request = RecommendationRequest(
            tickers=["AAPL"],
            horizon=Horizon.ONE_MONTH,
        )

        result = await recommendation_service.run(request, free_user)

        evidence = result.evidence[0]
        assert evidence.technical.rsi is not None
        assert evidence.technical.macd is not None
        assert evidence.technical.sma_50 is not None
        assert evidence.technical.current_price > 0

    @pytest.mark.asyncio
    async def test_evidence_has_fundamentals(self, recommendation_service, free_user):
        """Test evidence includes fundamental metrics."""
        request = RecommendationRequest(
            tickers=["AAPL"],
            horizon=Horizon.ONE_MONTH,
        )

        result = await recommendation_service.run(request, free_user)

        evidence = result.evidence[0]
        assert evidence.fundamental.pe_ratio is not None
        assert evidence.fundamental.revenue_growth is not None

    @pytest.mark.asyncio
    async def test_evidence_has_sentiment(self, recommendation_service, free_user):
        """Test evidence includes sentiment data."""
        request = RecommendationRequest(
            tickers=["AAPL"],
            horizon=Horizon.ONE_MONTH,
        )

        result = await recommendation_service.run(request, free_user)

        evidence = result.evidence[0]
        assert evidence.sentiment.score is not None
        assert evidence.sentiment.article_count >= 0

    @pytest.mark.asyncio
    async def test_evidence_has_attribution(self, recommendation_service, free_user):
        """Test evidence includes provider attribution."""
        request = RecommendationRequest(
            tickers=["AAPL"],
            horizon=Horizon.ONE_MONTH,
        )

        result = await recommendation_service.run(request, free_user)

        evidence = result.evidence[0]
        assert evidence.attribution is not None
        assert evidence.attribution.market_data_provider == "mock"
        assert evidence.attribution.fundamentals_provider == "mock"
        assert evidence.attribution.news_provider == "mock"

    @pytest.mark.asyncio
    async def test_evidence_has_news_articles(self, recommendation_service, free_user):
        """Test evidence includes news article summaries."""
        request = RecommendationRequest(
            tickers=["AAPL"],
            horizon=Horizon.ONE_MONTH,
        )

        result = await recommendation_service.run(request, free_user)

        evidence = result.evidence[0]
        assert evidence.news_articles is not None
        assert len(evidence.news_articles) <= 5  # Limited to 5 for UI

    @pytest.mark.asyncio
    async def test_attribution_timestamps_populated(self, recommendation_service, free_user):
        """Test that attribution timestamps are populated."""
        request = RecommendationRequest(
            tickers=["AAPL"],
            horizon=Horizon.ONE_MONTH,
        )

        result = await recommendation_service.run(request, free_user)

        evidence = result.evidence[0]
        assert evidence.attribution.market_data_fetched_at is not None
        assert evidence.attribution.fundamentals_fetched_at is not None
        assert evidence.attribution.news_fetched_at is not None
