"""NewsAPI news provider implementation."""

import logging
from datetime import datetime, timedelta, timezone

from adapters.cache import CacheEntry, ProviderCache, make_cache_key
from adapters.http_client import RetryingHttpClient
from domain.providers import NewsArticle, ProviderError

logger = logging.getLogger(__name__)

PROVIDER_NAME = "newsapi"

# Simple keyword-based sentiment detection
POSITIVE_KEYWORDS = {
    "surge",
    "soar",
    "jump",
    "gain",
    "rise",
    "rally",
    "beat",
    "exceed",
    "record",
    "growth",
    "upgrade",
    "bullish",
    "strong",
    "boost",
    "profit",
    "success",
    "breakthrough",
    "innovation",
    "optimistic",
    "expansion",
}

NEGATIVE_KEYWORDS = {
    "fall",
    "drop",
    "decline",
    "plunge",
    "crash",
    "loss",
    "miss",
    "downgrade",
    "bearish",
    "weak",
    "concern",
    "risk",
    "cut",
    "layoff",
    "investigation",
    "lawsuit",
    "warning",
    "recession",
    "slowdown",
    "trouble",
}


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
        self, ticker: str, max_articles: int = 20
    ) -> list[NewsArticle]:
        """Fetch recent news articles from NewsAPI.

        Args:
            ticker: Stock ticker symbol
            max_articles: Maximum number of articles to return

        Returns:
            List of NewsArticle objects with sentiment labels

        Raises:
            ProviderError: If news cannot be fetched
        """
        # Check cache first
        cache_key = make_cache_key(
            PROVIDER_NAME, "news", ticker, max_articles=max_articles
        )
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for {cache_key}")
            return self._deserialize_articles(cached.data)

        try:
            url = f"{self.base_url}/everything"

            # Search for articles mentioning the ticker
            # Use ticker as search query
            response = await self.http_client.get(
                url,
                params={
                    "q": ticker,
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
                url = article.get("url", "")
                description = article.get("description", "")

                # Compute simple sentiment label from title and description
                sentiment_label = self._compute_sentiment_label(
                    f"{title} {description}"
                )

                news_article = NewsArticle(
                    title=title,
                    source=source_name,
                    published_at=published_at,
                    url=url,
                    summary=description,
                )
                # Attach sentiment label as an extra attribute
                news_article.sentiment_label = sentiment_label  # type: ignore

                articles.append(news_article)

            # Cache the result
            now = datetime.now(timezone.utc)
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
            raise ProviderError(PROVIDER_NAME, ticker, str(e))

    def _compute_sentiment_label(self, text: str) -> str:
        """Compute a simple sentiment label from text.

        Args:
            text: Text to analyze

        Returns:
            "positive", "negative", or "neutral"
        """
        text_lower = text.lower()
        words = set(text_lower.split())

        positive_count = len(words & POSITIVE_KEYWORDS)
        negative_count = len(words & NEGATIVE_KEYWORDS)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
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
