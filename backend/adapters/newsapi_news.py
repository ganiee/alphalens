"""NewsAPI news provider implementation."""

import logging
from datetime import UTC, datetime, timedelta

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from adapters.cache import CacheEntry, ProviderCache, make_cache_key
from adapters.http_client import RetryingHttpClient
from domain.providers import NewsArticle, ProviderError

logger = logging.getLogger(__name__)

PROVIDER_NAME = "newsapi"

# VADER sentiment analyzer (initialized once)
_sentiment_analyzer = SentimentIntensityAnalyzer()

# Sentiment thresholds for VADER compound score (-1 to 1)
POSITIVE_THRESHOLD = 0.05
NEGATIVE_THRESHOLD = -0.05


class NewsAPINewsProvider:
    """News provider using NewsAPI.org."""

    def __init__(
        self,
        api_key: str,
        http_client: RetryingHttpClient,
        cache: ProviderCache,
        cache_ttl_seconds: int = 300,
        base_url: str = "https://newsapi.org/v2",
        page_size: int = 8,
    ):
        """Initialize the NewsAPI provider.

        Args:
            api_key: NewsAPI API key
            http_client: HTTP client for making requests
            cache: Provider cache for storing responses
            cache_ttl_seconds: Cache TTL in seconds (default 5 minutes)
            base_url: NewsAPI base URL
            page_size: Number of articles to fetch per request
        """
        self.api_key = api_key
        self.http_client = http_client
        self.cache = cache
        self.cache_ttl_seconds = cache_ttl_seconds
        self.base_url = base_url
        self.page_size = page_size

    async def get_news(
        self, ticker: str, max_articles: int = 20, company_name: str | None = None
    ) -> list[NewsArticle]:
        """Fetch recent news articles from NewsAPI.

        Args:
            ticker: Stock ticker symbol
            max_articles: Maximum number of articles to return
            company_name: Optional company name for better search relevance

        Returns:
            List of NewsArticle objects with sentiment labels

        Raises:
            ProviderError: If news cannot be fetched
        """
        # Check cache first
        cache_key = make_cache_key(PROVIDER_NAME, "news", ticker, max_articles=max_articles)
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for {cache_key}")
            return self._deserialize_articles(cached.data)

        try:
            # Build search queries - try company name first, then fall back to ticker
            queries_to_try = []

            if company_name and company_name != ticker:
                # Remove common suffixes for cleaner search
                clean_name = (
                    company_name.replace(".Com", "")
                    .replace(".com", "")
                    .replace(" Inc.", "")
                    .replace(" Inc", "")
                    .replace(" Corp.", "")
                    .replace(" Corp", "")
                    .replace(" Corporation", "")
                    .replace(", Inc.", "")
                    .replace(" Ltd.", "")
                    .replace(" Ltd", "")
                    .replace(" LLC", "")
                    .replace(" PLC", "")
                    .strip()
                )
                # Primary: company name AND ticker for precise matching
                queries_to_try.append(f'"{clean_name}" AND {ticker}')

            # Fallback: ticker with stock context
            queries_to_try.append(f'"{ticker}" AND (stock OR shares OR earnings)')

            articles = []
            for search_query in queries_to_try:
                logger.debug(f"NewsAPI search query for {ticker}: {search_query}")
                articles = await self._fetch_articles(ticker, search_query, max_articles)

                if articles:
                    logger.info(
                        f"Found {len(articles)} articles for {ticker} with query: {search_query}"
                    )
                    break
                else:
                    logger.debug(f"No results for {ticker} with query: {search_query}, trying next")

            # Cache the result (even if empty)
            now = datetime.now(UTC)
            self.cache.set(
                CacheEntry(
                    cache_key=cache_key,
                    provider=PROVIDER_NAME,
                    data=self._serialize_articles(articles),
                    ticker=ticker,
                    fetched_at=now,
                    expires_at=now + timedelta(seconds=self.cache_ttl_seconds),
                )
            )

            logger.info(f"Fetched {len(articles)} news articles for {ticker} from NewsAPI")
            return articles

        except ProviderError:
            raise
        except Exception as e:
            logger.error(f"NewsAPI error for {ticker}: {e}")
            raise ProviderError(PROVIDER_NAME, ticker, str(e)) from e

    async def _fetch_articles(
        self, ticker: str, search_query: str, max_articles: int
    ) -> list[NewsArticle]:
        """Fetch articles for a specific search query.

        Args:
            ticker: Stock ticker symbol (for error reporting)
            search_query: The search query to use
            max_articles: Maximum number of articles to return

        Returns:
            List of NewsArticle objects
        """
        url = f"{self.base_url}/everything"

        response = await self.http_client.get(
            url,
            params={
                "q": search_query,
                "sortBy": "publishedAt",
                "pageSize": min(self.page_size, max_articles),
                "language": "en",
            },
            headers={"X-Api-Key": self.api_key},
        )

        data = response.json()

        if data.get("status") == "error":
            raise ProviderError(
                PROVIDER_NAME,
                ticker,
                data.get("message", "Unknown API error"),
            )

        raw_articles = data.get("articles", [])

        # Parse articles
        articles = []
        for article in raw_articles[:max_articles]:
            title = article.get("title", "")
            source_info = article.get("source", {})
            source_name = source_info.get("name", "Unknown")
            published_at = article.get("publishedAt", "")
            article_url = article.get("url", "")
            description = article.get("description", "")

            # Compute simple sentiment label from title and description
            sentiment_label = self._compute_sentiment_label(f"{title} {description}")

            news_article = NewsArticle(
                title=title,
                source=source_name,
                published_at=published_at,
                url=article_url,
                summary=description,
            )
            # Attach sentiment label as an extra attribute
            news_article.sentiment_label = sentiment_label  # type: ignore

            articles.append(news_article)

        return articles

    def _compute_sentiment_label(self, text: str) -> str:
        """Compute sentiment label using VADER sentiment analyzer.

        VADER (Valence Aware Dictionary and sEntiment Reasoner) is specifically
        designed for social media and news text. It handles:
        - Negations ("not good" → negative)
        - Intensifiers ("very good" → more positive)
        - Punctuation and capitalization
        - Emoticons and slang

        Args:
            text: Text to analyze

        Returns:
            "positive", "negative", or "neutral"
        """
        if not text or not text.strip():
            return "neutral"

        # Get VADER sentiment scores
        scores = _sentiment_analyzer.polarity_scores(text)
        compound = scores["compound"]  # Normalized score from -1 to 1

        # Classify based on compound score
        if compound >= POSITIVE_THRESHOLD:
            return "positive"
        elif compound <= NEGATIVE_THRESHOLD:
            return "negative"
        else:
            return "neutral"

    def _serialize_articles(self, articles: list[NewsArticle]) -> dict:
        """Serialize articles for caching."""
        return {
            "articles": [
                {
                    "title": a.title,
                    "source": a.source,
                    "published_at": a.published_at,
                    "url": a.url,
                    "summary": a.summary,
                    "sentiment_label": getattr(a, "sentiment_label", "neutral"),
                }
                for a in articles
            ]
        }

    def _deserialize_articles(self, data: dict) -> list[NewsArticle]:
        """Deserialize articles from cache."""
        articles = []
        for item in data.get("articles", []):
            article = NewsArticle(
                title=item["title"],
                source=item["source"],
                published_at=item["published_at"],
                url=item["url"],
                summary=item.get("summary"),
            )
            article.sentiment_label = item.get("sentiment_label", "neutral")  # type: ignore
            articles.append(article)
        return articles
