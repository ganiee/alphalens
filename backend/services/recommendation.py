"""Recommendation service - orchestrates the scoring pipeline."""

import asyncio
import logging
from datetime import UTC, datetime

from adapters.mock_fundamentals import MockFundamentalsProvider
from adapters.mock_market_data import MockMarketDataProvider
from adapters.mock_news import MockNewsProvider
from adapters.newsapi_news import NewsAPINewsProvider
from adapters.polygon_market_data import PolygonMarketDataProvider
from adapters.yfinance_fundamentals import YFinanceFundamentalsProvider
from domain.auth import User
from domain.providers import (
    FundamentalsProvider,
    InvalidTickerError,
    MarketDataProvider,
    NewsProvider,
    ProviderError,
    SentimentAnalyzer,
)
from domain.recommendation import (
    CompanyInfo,
    EvidencePacket,
    NewsArticleSummary,
    ProviderAttribution,
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

logger = logging.getLogger(__name__)


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
            created_at=datetime.now(UTC),
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

        Uses fallback to mock providers if real providers fail.

        Args:
            ticker: Stock ticker symbol

        Returns:
            EvidencePacket with all fetched data
        """
        now = datetime.now(UTC)

        # Initialize attribution tracking
        attribution = ProviderAttribution()

        # Fetch price history with fallback
        price_history = await self._fetch_with_fallback(
            primary=self.market_data.get_price_history(ticker, days=200),
            fallback_provider=MockMarketDataProvider(),
            fallback_call=lambda p: p.get_price_history(ticker, days=200),
            provider_name=self._get_provider_name(self.market_data),
        )
        attribution.market_data_provider = self._get_provider_name(self.market_data)
        attribution.market_data_fetched_at = now

        # Fetch fundamentals with fallback
        fundamentals = await self._fetch_with_fallback(
            primary=self.fundamentals.get_fundamentals(ticker),
            fallback_provider=MockFundamentalsProvider(),
            fallback_call=lambda p: p.get_fundamentals(ticker),
            provider_name=self._get_provider_name(self.fundamentals),
        )
        attribution.fundamentals_provider = self._get_provider_name(self.fundamentals)
        attribution.fundamentals_fetched_at = now

        # Fetch company info (uses market data provider - Polygon has this data)
        try:
            company_info = await self.market_data.get_company_info(ticker)
        except Exception as e:
            logger.warning(f"Failed to fetch company info for {ticker}: {e}")
            company_info = CompanyInfo(name=ticker)

        # Fetch news with fallback (pass company name for better search relevance)
        news_articles = await self._fetch_with_fallback(
            primary=self.news.get_news(
                ticker, max_articles=5, company_name=company_info.name
            ),
            fallback_provider=MockNewsProvider(),
            fallback_call=lambda p: p.get_news(
                ticker, max_articles=5, company_name=company_info.name
            ),
            provider_name=self._get_provider_name(self.news),
        )
        attribution.news_provider = self._get_provider_name(self.news)
        attribution.news_fetched_at = now

        # Compute technical indicators from price history
        technical = compute_technical_indicators(price_history)

        # Analyze sentiment from news
        sentiment = await self.sentiment.analyze_sentiment(ticker, news_articles)

        # Convert news articles to summaries for UI
        article_summaries = [
            NewsArticleSummary(
                title=article.title,
                source=article.source,
                published_at=article.published_at,
                url=article.url,
                sentiment_label=getattr(article, "sentiment_label", None),
            )
            for article in news_articles[:5]  # Limit to 5 for UI
        ]

        return EvidencePacket(
            ticker=ticker,
            company_info=company_info,
            technical=technical,
            fundamental=fundamentals,
            sentiment=sentiment,
            fetched_at=now,
            news_articles=article_summaries,
            attribution=attribution,
        )

    async def _fetch_with_fallback(
        self,
        primary,
        fallback_provider,
        fallback_call,
        provider_name: str,
    ):
        """Execute a fetch with fallback to mock provider on failure.

        Args:
            primary: Primary coroutine to execute
            fallback_provider: Fallback provider instance
            fallback_call: Callable to invoke on fallback provider
            provider_name: Name of the primary provider (for logging)

        Returns:
            Result from primary or fallback

        Raises:
            InvalidTickerError: If the ticker does not exist (no fallback)
        """
        try:
            return await primary
        except InvalidTickerError:
            # Don't fallback for invalid tickers - let it propagate
            raise
        except ProviderError as e:
            logger.warning(
                f"Provider {provider_name} failed, falling back to mock: {e}"
            )
            return await fallback_call(fallback_provider)
        except Exception as e:
            logger.warning(
                f"Unexpected error from {provider_name}, falling back to mock: {e}"
            )
            return await fallback_call(fallback_provider)

    def _get_provider_name(self, provider) -> str:
        """Get the display name for a provider.

        Args:
            provider: Provider instance

        Returns:
            Human-readable provider name
        """
        if isinstance(provider, PolygonMarketDataProvider):
            return "Polygon"
        elif isinstance(provider, YFinanceFundamentalsProvider):
            return "Yahoo Finance"
        elif isinstance(provider, NewsAPINewsProvider):
            return "NewsAPI"
        elif isinstance(
            provider, (MockMarketDataProvider, MockFundamentalsProvider, MockNewsProvider)
        ):
            return "mock"
        else:
            return "unknown"

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
