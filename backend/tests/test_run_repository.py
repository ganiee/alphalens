"""Tests for RunRepository interface and implementations (F1-10)."""

import pytest

from domain.recommendation import (
    EvidencePacket,
    FundamentalMetrics,
    Horizon,
    RecommendationResult,
    ScoreBreakdown,
    SentimentData,
    StockScore,
    TechnicalIndicators,
)
from domain.run_repository import RunRepository
from repo.recommendations import InMemoryRunRepository, get_recommendation_repository


def create_test_result(
    user_id: str = "test-user-123",
    tickers: list[str] | None = None,
    run_id: str | None = None,
) -> RecommendationResult:
    """Create a test recommendation result."""
    if tickers is None:
        tickers = ["AAPL"]

    scores = [
        StockScore(
            ticker=ticker,
            composite_score=75.0 + i * 5,
            breakdown=ScoreBreakdown(technical=80.0, fundamental=70.0, sentiment=75.0),
            rank=i + 1,
            allocation_pct=100.0 / len(tickers),
        )
        for i, ticker in enumerate(tickers)
    ]

    evidence = [
        EvidencePacket(
            ticker=ticker,
            technical=TechnicalIndicators(
                rsi=50.0,
                macd=1.0,
                macd_signal=0.8,
                macd_histogram=0.2,
                sma_50=150.0,
                sma_200=140.0,
                current_price=155.0,
                volume_trend=1.1,
            ),
            fundamental=FundamentalMetrics(
                pe_ratio=25.0,
                revenue_growth=0.15,
                profit_margin=0.20,
                debt_to_equity=0.5,
                market_cap=2_500_000_000_000,
            ),
            sentiment=SentimentData(
                score=0.3,
                article_count=10,
                positive_count=6,
                negative_count=2,
                neutral_count=2,
            ),
        )
        for ticker in tickers
    ]

    result = RecommendationResult(
        user_id=user_id,
        tickers=tickers,
        horizon=Horizon.ONE_MONTH,
        scores=scores,
        evidence=evidence,
    )

    if run_id:
        result.run_id = run_id

    return result


class TestRunRepositoryProtocol:
    """Tests for RunRepository Protocol compliance."""

    def test_in_memory_implements_protocol(self):
        """InMemoryRunRepository implements RunRepository protocol."""
        repo = InMemoryRunRepository()
        assert isinstance(repo, RunRepository)

    def test_singleton_implements_protocol(self):
        """Singleton getter returns RunRepository implementation."""
        repo = get_recommendation_repository()
        assert isinstance(repo, RunRepository)


class TestInMemoryRunRepository:
    """Tests for InMemoryRunRepository implementation."""

    @pytest.fixture
    def repo(self):
        """Create a fresh repository for each test."""
        repo = InMemoryRunRepository()
        yield repo
        repo.clear()

    def test_save_returns_run_id(self, repo):
        """Save returns the run_id."""
        result = create_test_result()
        run_id = repo.save(result)

        assert run_id == result.run_id
        assert len(run_id) > 0

    def test_get_by_id_returns_result(self, repo):
        """Get by ID returns the saved result."""
        result = create_test_result()
        repo.save(result)

        retrieved = repo.get_by_id(result.run_id)

        assert retrieved is not None
        assert retrieved.run_id == result.run_id
        assert retrieved.user_id == result.user_id
        assert retrieved.tickers == result.tickers

    def test_get_by_id_returns_none_for_missing(self, repo):
        """Get by ID returns None for non-existent run."""
        retrieved = repo.get_by_id("non-existent-id")
        assert retrieved is None

    def test_get_by_user_filters_by_user_id(self, repo):
        """Get by user only returns that user's results."""
        # Create results for two users
        result1 = create_test_result(user_id="user-1", tickers=["AAPL"])
        result2 = create_test_result(user_id="user-2", tickers=["MSFT"])
        result3 = create_test_result(user_id="user-1", tickers=["GOOGL"])

        repo.save(result1)
        repo.save(result2)
        repo.save(result3)

        # Get user-1's results
        summaries = repo.get_by_user("user-1")

        assert len(summaries) == 2
        tickers = [s.tickers[0] for s in summaries]
        assert "AAPL" in tickers
        assert "GOOGL" in tickers
        assert "MSFT" not in tickers

    def test_get_by_user_returns_empty_for_no_results(self, repo):
        """Get by user returns empty list for user with no results."""
        summaries = repo.get_by_user("non-existent-user")
        assert summaries == []

    def test_get_by_user_pagination(self, repo):
        """Get by user supports pagination."""
        # Create 5 results for one user
        for i in range(5):
            result = create_test_result(user_id="user-1", tickers=[f"TKR{i}"])
            repo.save(result)

        # Get with limit
        page1 = repo.get_by_user("user-1", limit=2, offset=0)
        page2 = repo.get_by_user("user-1", limit=2, offset=2)
        page3 = repo.get_by_user("user-1", limit=2, offset=4)

        assert len(page1) == 2
        assert len(page2) == 2
        assert len(page3) == 1

    def test_get_by_user_sorted_newest_first(self, repo):
        """Get by user returns results sorted by created_at, newest first."""
        # Create results with different timestamps
        result1 = create_test_result(user_id="user-1", tickers=["FIRST"])
        result2 = create_test_result(user_id="user-1", tickers=["SECOND"])
        result3 = create_test_result(user_id="user-1", tickers=["THIRD"])

        # Save in order
        repo.save(result1)
        repo.save(result2)
        repo.save(result3)

        summaries = repo.get_by_user("user-1")

        # Most recent (THIRD) should be first
        assert summaries[0].tickers == ["THIRD"]
        assert summaries[2].tickers == ["FIRST"]

    def test_delete_removes_result(self, repo):
        """Delete removes the result from storage."""
        result = create_test_result()
        repo.save(result)

        deleted = repo.delete(result.run_id)

        assert deleted is True
        assert repo.get_by_id(result.run_id) is None

    def test_delete_returns_false_for_missing(self, repo):
        """Delete returns False for non-existent run."""
        deleted = repo.delete("non-existent-id")
        assert deleted is False

    def test_clear_removes_all_results(self, repo):
        """Clear removes all results."""
        repo.save(create_test_result(user_id="user-1"))
        repo.save(create_test_result(user_id="user-2"))

        repo.clear()

        assert repo.get_by_user("user-1") == []
        assert repo.get_by_user("user-2") == []

    def test_summary_includes_top_pick(self, repo):
        """Summary includes top pick and score."""
        result = create_test_result(tickers=["AAPL", "MSFT"])
        repo.save(result)

        summaries = repo.get_by_user(result.user_id)

        assert len(summaries) == 1
        summary = summaries[0]
        assert summary.top_pick == "AAPL"  # First ticker with highest score
        assert summary.top_score is not None
        assert summary.top_score > 0


class TestAuthAnalyzeIntegration:
    """Integration tests for auth-analyze flow (F1-10)."""

    @pytest.fixture(autouse=True)
    def clear_singleton(self):
        """Clear the singleton repository before/after each test."""
        repo = get_recommendation_repository()
        repo.clear()
        yield
        repo.clear()

    def test_user_can_save_and_retrieve_own_result(self):
        """User can save and retrieve their own result."""
        repo = get_recommendation_repository()
        user_id = "cognito-sub-12345"

        result = create_test_result(user_id=user_id, tickers=["AAPL"])
        run_id = repo.save(result)

        retrieved = repo.get_by_id(run_id)
        assert retrieved is not None
        assert retrieved.user_id == user_id

    def test_user_history_is_isolated(self):
        """Each user only sees their own history."""
        repo = get_recommendation_repository()

        # User A creates a result
        result_a = create_test_result(user_id="user-a", tickers=["AAPL"])
        repo.save(result_a)

        # User B creates a result
        result_b = create_test_result(user_id="user-b", tickers=["MSFT"])
        repo.save(result_b)

        # User A only sees their result
        history_a = repo.get_by_user("user-a")
        assert len(history_a) == 1
        assert history_a[0].tickers == ["AAPL"]

        # User B only sees their result
        history_b = repo.get_by_user("user-b")
        assert len(history_b) == 1
        assert history_b[0].tickers == ["MSFT"]

    def test_result_contains_user_id(self):
        """Saved result contains the user_id for attribution."""
        repo = get_recommendation_repository()
        user_id = "cognito-sub-67890"

        result = create_test_result(user_id=user_id)
        repo.save(result)

        retrieved = repo.get_by_id(result.run_id)
        assert retrieved.user_id == user_id
