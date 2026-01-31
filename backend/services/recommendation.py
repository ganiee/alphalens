"""Recommendation service - orchestrates the scoring pipeline."""

import asyncio
from datetime import datetime

from domain.auth import User
from domain.providers import (
    FundamentalsProvider,
    MarketDataProvider,
    NewsProvider,
    SentimentAnalyzer,
)
from domain.recommendation import (
    EvidencePacket,
    RecommendationRequest,
    RecommendationResult,
    ScoreBreakdown,
    validate_request_for_plan,
)
from services.indicators import compute_technical_indicators
from services.scoring import (
    calculate_fundamental_score,
    calculate_sentiment_score,
    calculate_technical_score,
    rank_and_allocate,
)


class RecommendationService:
    """Orchestrates the recommendation pipeline.

    Pipeline: FetchData → ComputeFeatures → Score → Rank → Allocate
    """

    def __init__(
        self,
        market_data: MarketDataProvider,
        fundamentals: FundamentalsProvider,
        news: NewsProvider,
        sentiment: SentimentAnalyzer,
    ):
        """Initialize with provider dependencies.

        Args:
            market_data: Provider for price history
            fundamentals: Provider for financial metrics
            news: Provider for news articles
            sentiment: Analyzer for sentiment scoring
        """
        self.market_data = market_data
        self.fundamentals = fundamentals
        self.news = news
        self.sentiment = sentiment

    async def run(
        self,
        request: RecommendationRequest,
        user: User,
    ) -> RecommendationResult:
        """Execute the recommendation pipeline.

        Args:
            request: The recommendation request with tickers and horizon
            user: The authenticated user making the request

        Returns:
            RecommendationResult with scores, rankings, and evidence

        Raises:
            PlanConstraintError: If request violates user's plan limits
        """
        # Validate request against user's plan
        validate_request_for_plan(request, user.plan)

        # Fetch data for all tickers in parallel
        evidence_packets = await self._fetch_all_data(request.tickers)

        # Calculate scores for each ticker
        ticker_scores: list[tuple[str, ScoreBreakdown]] = []
        for evidence in evidence_packets:
            breakdown = self._calculate_scores(evidence)
            ticker_scores.append((evidence.ticker, breakdown))

        # Rank and allocate
        stock_scores = rank_and_allocate(ticker_scores)

        return RecommendationResult(
            user_id=user.sub,
            tickers=request.tickers,
            horizon=request.horizon,
            scores=stock_scores,
            evidence=evidence_packets,
            created_at=datetime.utcnow(),
        )

    async def _fetch_all_data(self, tickers: list[str]) -> list[EvidencePacket]:
        """Fetch all data for multiple tickers in parallel.

        Args:
            tickers: List of ticker symbols

        Returns:
            List of EvidencePacket for each ticker
        """
        tasks = [self._fetch_ticker_data(ticker) for ticker in tickers]
        return await asyncio.gather(*tasks)

    async def _fetch_ticker_data(self, ticker: str) -> EvidencePacket:
        """Fetch all data for a single ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            EvidencePacket with all fetched data
        """
        # Fetch all data sources in parallel
        price_history, fundamentals, news_articles = await asyncio.gather(
            self.market_data.get_price_history(ticker, days=200),
            self.fundamentals.get_fundamentals(ticker),
            self.news.get_news(ticker, max_articles=20),
        )

        # Compute technical indicators from price history
        technical = compute_technical_indicators(price_history)

        # Analyze sentiment from news
        sentiment = await self.sentiment.analyze_sentiment(ticker, news_articles)

        return EvidencePacket(
            ticker=ticker,
            technical=technical,
            fundamental=fundamentals,
            sentiment=sentiment,
            fetched_at=datetime.utcnow(),
        )

    def _calculate_scores(self, evidence: EvidencePacket) -> ScoreBreakdown:
        """Calculate all score components for a ticker.

        Args:
            evidence: Evidence packet with all fetched data

        Returns:
            ScoreBreakdown with technical, fundamental, and sentiment scores
        """
        technical_score = calculate_technical_score(evidence.technical)
        fundamental_score = calculate_fundamental_score(evidence.fundamental)
        sentiment_score = calculate_sentiment_score(evidence.sentiment)

        return ScoreBreakdown(
            technical=technical_score,
            fundamental=fundamental_score,
            sentiment=sentiment_score,
        )
