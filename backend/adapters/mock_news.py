"""Mock news provider for testing and development."""

from datetime import datetime, timedelta

from domain.providers import NewsArticle

# Mock news templates for different sentiment types
POSITIVE_NEWS_TEMPLATES = [
    "{ticker} reports record quarterly earnings, beating analyst expectations",
    "{ticker} announces major partnership with industry leader",
    "{ticker} stock upgraded by multiple analysts to 'Buy'",
    "{ticker} unveils innovative new product line",
    "{ticker} expands into emerging markets with strong growth potential",
    "Institutional investors increase {ticker} holdings significantly",
]

NEGATIVE_NEWS_TEMPLATES = [
    "{ticker} misses earnings estimates, stock under pressure",
    "{ticker} faces regulatory investigation, shares decline",
    "{ticker} announces layoffs amid cost-cutting measures",
    "{ticker} loses major contract to competitor",
    "Analysts downgrade {ticker} citing growth concerns",
    "{ticker} recalls products due to safety issues",
]

NEUTRAL_NEWS_TEMPLATES = [
    "{ticker} to report earnings next week, analysts mixed",
    "{ticker} CEO speaks at industry conference",
    "{ticker} announces board member retirement",
    "{ticker} maintains guidance for fiscal year",
    "{ticker} completes routine acquisition",
    "Market analysts provide mixed outlook for {ticker}",
]

NEWS_SOURCES = [
    "Reuters",
    "Bloomberg",
    "CNBC",
    "Wall Street Journal",
    "Financial Times",
    "MarketWatch",
]


def _generate_article(
    ticker: str,
    template: str,
    sentiment: str,
    index: int,
    base_date: datetime,
) -> NewsArticle:
    """Generate a mock news article."""
    title = template.format(ticker=ticker)
    source = NEWS_SOURCES[index % len(NEWS_SOURCES)]
    published = base_date - timedelta(days=index, hours=index * 3)

    return NewsArticle(
        title=title,
        source=source,
        published_at=published.isoformat(),
        url=f"https://example.com/news/{ticker.lower()}-{index}",
        summary=f"Mock summary for {ticker} {sentiment} news article #{index}",
    )


# Predefined sentiment distribution by ticker
TICKER_SENTIMENT_BIAS = {
    "AAPL": 0.6,   # Slightly positive
    "MSFT": 0.7,   # Positive
    "GOOGL": 0.5,  # Neutral
    "AMZN": 0.55,  # Slightly positive
    "NVDA": 0.8,   # Very positive
    "META": 0.4,   # Slightly negative
    "TSLA": 0.45,  # Mixed/slightly negative
    "JPM": 0.5,    # Neutral
    "V": 0.6,      # Slightly positive
    "JNJ": 0.55,   # Slightly positive
}


class MockNewsProvider:
    """Mock implementation of NewsProvider for testing."""

    async def get_news(self, ticker: str, max_articles: int = 20) -> list[NewsArticle]:
        """Return mock news articles for a ticker.

        Args:
            ticker: Stock ticker symbol
            max_articles: Maximum number of articles to return

        Returns:
            List of mock NewsArticle objects
        """
        ticker = ticker.upper()

        # Get sentiment bias for ticker (default 0.5 = neutral)
        ticker_hash = sum(ord(c) for c in ticker)
        bias = TICKER_SENTIMENT_BIAS.get(ticker, 0.5 + (ticker_hash % 20 - 10) * 0.02)

        # Calculate article distribution
        positive_count = int(max_articles * bias * 0.6)
        negative_count = int(max_articles * (1 - bias) * 0.6)
        neutral_count = max_articles - positive_count - negative_count

        articles = []
        base_date = datetime(2024, 1, 15, 12, 0, 0)  # Fixed date for determinism
        article_index = 0

        # Generate positive articles
        for i in range(positive_count):
            template = POSITIVE_NEWS_TEMPLATES[i % len(POSITIVE_NEWS_TEMPLATES)]
            articles.append(
                _generate_article(ticker, template, "positive", article_index, base_date)
            )
            article_index += 1

        # Generate negative articles
        for i in range(negative_count):
            template = NEGATIVE_NEWS_TEMPLATES[i % len(NEGATIVE_NEWS_TEMPLATES)]
            articles.append(
                _generate_article(ticker, template, "negative", article_index, base_date)
            )
            article_index += 1

        # Generate neutral articles
        for i in range(neutral_count):
            template = NEUTRAL_NEWS_TEMPLATES[i % len(NEUTRAL_NEWS_TEMPLATES)]
            articles.append(
                _generate_article(ticker, template, "neutral", article_index, base_date)
            )
            article_index += 1

        # Sort by published date (most recent first)
        articles.sort(key=lambda a: a.published_at, reverse=True)

        return articles[:max_articles]
