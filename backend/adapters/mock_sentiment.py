"""Mock sentiment analyzer for testing and development."""

from domain.providers import NewsArticle
from domain.recommendation import SentimentData

# Keywords indicating positive sentiment
POSITIVE_KEYWORDS = [
    "record", "beat", "exceed", "growth", "upgrade", "buy",
    "innovative", "expand", "increase", "strong", "success",
    "partnership", "opportunity", "momentum", "outperform",
]

# Keywords indicating negative sentiment
NEGATIVE_KEYWORDS = [
    "miss", "decline", "downgrade", "sell", "concern", "pressure",
    "layoff", "investigation", "recall", "loss", "weak", "fail",
    "regulatory", "lawsuit", "cut", "warning", "underperform",
]


def _analyze_article_sentiment(article: NewsArticle) -> float:
    """Analyze sentiment of a single article.

    Returns:
        Sentiment score from -1 (very negative) to 1 (very positive)
    """
    text = (article.title + " " + (article.summary or "")).lower()

    positive_count = sum(1 for word in POSITIVE_KEYWORDS if word in text)
    negative_count = sum(1 for word in NEGATIVE_KEYWORDS if word in text)

    total = positive_count + negative_count
    if total == 0:
        return 0.0  # Neutral

    # Score from -1 to 1
    score = (positive_count - negative_count) / total
    return max(-1.0, min(1.0, score))


class MockSentimentAnalyzer:
    """Mock implementation of SentimentAnalyzer for testing."""

    async def analyze_sentiment(
        self, ticker: str, articles: list[NewsArticle]
    ) -> SentimentData:
        """Analyze sentiment from news articles.

        Args:
            ticker: Stock ticker symbol (for logging/context)
            articles: List of news articles to analyze

        Returns:
            SentimentData with aggregated scores
        """
        if not articles:
            return SentimentData(
                score=0.0,
                article_count=0,
                positive_count=0,
                negative_count=0,
                neutral_count=0,
            )

        positive_count = 0
        negative_count = 0
        neutral_count = 0
        total_score = 0.0

        for article in articles:
            article_score = _analyze_article_sentiment(article)
            total_score += article_score

            if article_score > 0.2:
                positive_count += 1
            elif article_score < -0.2:
                negative_count += 1
            else:
                neutral_count += 1

        # Average score across all articles
        avg_score = total_score / len(articles)

        return SentimentData(
            score=round(avg_score, 3),
            article_count=len(articles),
            positive_count=positive_count,
            negative_count=negative_count,
            neutral_count=neutral_count,
        )
