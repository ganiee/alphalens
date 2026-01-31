"""Scoring algorithms for stock analysis."""

from domain.recommendation import (
    FundamentalMetrics,
    ScoreBreakdown,
    SentimentData,
    StockScore,
    TechnicalIndicators,
)

# Scoring weights for composite score
TECHNICAL_WEIGHT = 0.40
FUNDAMENTAL_WEIGHT = 0.30
SENTIMENT_WEIGHT = 0.30


def _normalize_score(value: float, min_val: float, max_val: float) -> float:
    """Normalize a value to 0-100 range.

    Args:
        value: The value to normalize
        min_val: Minimum expected value (maps to 0)
        max_val: Maximum expected value (maps to 100)

    Returns:
        Normalized score between 0 and 100
    """
    if max_val == min_val:
        return 50.0
    normalized = (value - min_val) / (max_val - min_val) * 100
    return max(0.0, min(100.0, normalized))


def calculate_technical_score(indicators: TechnicalIndicators) -> float:
    """Calculate technical analysis score (0-100).

    Scoring criteria:
    - RSI: Oversold (< 30) = bullish, Overbought (> 70) = bearish
    - MACD: Positive histogram = bullish
    - Price vs SMA: Above SMA50/200 = bullish
    - Volume trend: Increasing = bullish

    Args:
        indicators: Technical indicators for the stock

    Returns:
        Technical score between 0 and 100
    """
    score = 0.0

    # RSI component (25 points max)
    # Oversold = bullish, Overbought = bearish
    if indicators.rsi < 30:
        rsi_score = 25  # Oversold - strong buy signal
    elif indicators.rsi < 40:
        rsi_score = 20  # Approaching oversold
    elif indicators.rsi > 70:
        rsi_score = 5   # Overbought - sell signal
    elif indicators.rsi > 60:
        rsi_score = 10  # Approaching overbought
    else:
        rsi_score = 15  # Neutral zone
    score += rsi_score

    # MACD component (25 points max)
    # Positive histogram = bullish momentum
    if indicators.macd_histogram > 0.5:
        macd_score = 25  # Strong bullish momentum
    elif indicators.macd_histogram > 0:
        macd_score = 20  # Bullish momentum
    elif indicators.macd_histogram > -0.5:
        macd_score = 10  # Weak bearish momentum
    else:
        macd_score = 5   # Strong bearish momentum
    score += macd_score

    # Price vs SMA component (30 points max)
    price = indicators.current_price
    above_sma50 = price > indicators.sma_50
    above_sma200 = price > indicators.sma_200

    if above_sma50 and above_sma200:
        sma_score = 30  # Strong uptrend
    elif above_sma200:
        sma_score = 20  # Medium-term uptrend
    elif above_sma50:
        sma_score = 15  # Short-term recovery
    else:
        sma_score = 5   # Downtrend

    # Golden cross / Death cross bonus
    if indicators.sma_50 > indicators.sma_200:
        sma_score = min(30, sma_score + 5)  # Golden cross bonus
    score += sma_score

    # Volume trend component (20 points max)
    if indicators.volume_trend > 1.2:
        volume_score = 20  # Strong increasing volume
    elif indicators.volume_trend > 1.0:
        volume_score = 15  # Increasing volume
    elif indicators.volume_trend > 0.8:
        volume_score = 10  # Stable volume
    else:
        volume_score = 5   # Decreasing volume
    score += volume_score

    return round(score, 2)


def calculate_fundamental_score(metrics: FundamentalMetrics) -> float:
    """Calculate fundamental analysis score (0-100).

    Scoring criteria:
    - P/E ratio: Lower is better (relative to market)
    - Revenue growth: Higher is better
    - Profit margin: Higher is better
    - Debt/Equity: Lower is better

    Args:
        metrics: Fundamental metrics for the stock

    Returns:
        Fundamental score between 0 and 100
    """
    score = 0.0
    components = 0

    # P/E ratio component (25 points max)
    # Market average P/E is roughly 20-25
    if metrics.pe_ratio is not None:
        if metrics.pe_ratio < 0:
            pe_score = 5   # Negative earnings
        elif metrics.pe_ratio < 15:
            pe_score = 25  # Undervalued
        elif metrics.pe_ratio < 25:
            pe_score = 20  # Fair value
        elif metrics.pe_ratio < 40:
            pe_score = 12  # Growth premium
        else:
            pe_score = 5   # Overvalued
        score += pe_score
        components += 1

    # Revenue growth component (25 points max)
    if metrics.revenue_growth is not None:
        if metrics.revenue_growth > 0.20:
            growth_score = 25  # High growth
        elif metrics.revenue_growth > 0.10:
            growth_score = 20  # Good growth
        elif metrics.revenue_growth > 0.05:
            growth_score = 15  # Moderate growth
        elif metrics.revenue_growth > 0:
            growth_score = 10  # Low growth
        else:
            growth_score = 5   # Declining
        score += growth_score
        components += 1

    # Profit margin component (25 points max)
    if metrics.profit_margin is not None:
        if metrics.profit_margin > 0.25:
            margin_score = 25  # Excellent margins
        elif metrics.profit_margin > 0.15:
            margin_score = 20  # Good margins
        elif metrics.profit_margin > 0.08:
            margin_score = 15  # Average margins
        elif metrics.profit_margin > 0:
            margin_score = 10  # Low margins
        else:
            margin_score = 5   # Unprofitable
        score += margin_score
        components += 1

    # Debt/Equity component (25 points max)
    if metrics.debt_to_equity is not None:
        if metrics.debt_to_equity < 0.3:
            debt_score = 25  # Very low debt
        elif metrics.debt_to_equity < 0.6:
            debt_score = 20  # Low debt
        elif metrics.debt_to_equity < 1.0:
            debt_score = 15  # Moderate debt
        elif metrics.debt_to_equity < 2.0:
            debt_score = 10  # High debt
        else:
            debt_score = 5   # Very high debt
        score += debt_score
        components += 1

    # Normalize if not all components available
    if components > 0 and components < 4:
        score = score * (4 / components)

    return round(min(100.0, score), 2)


def calculate_sentiment_score(sentiment: SentimentData) -> float:
    """Calculate sentiment analysis score (0-100).

    Scoring criteria:
    - Sentiment score: -1 to 1 mapped to 0-100
    - Article volume factor: More articles = more confidence

    Args:
        sentiment: Sentiment data from news analysis

    Returns:
        Sentiment score between 0 and 100
    """
    # Base score from sentiment (-1 to 1 → 0 to 100)
    base_score = (sentiment.score + 1) / 2 * 100

    # Volume confidence factor
    # More articles = more reliable signal
    if sentiment.article_count >= 15:
        confidence = 1.0
    elif sentiment.article_count >= 10:
        confidence = 0.9
    elif sentiment.article_count >= 5:
        confidence = 0.8
    else:
        # Low article count - regress toward neutral
        confidence = 0.6

    # Apply confidence (pulls score toward 50 if low confidence)
    adjusted_score = 50 + (base_score - 50) * confidence

    return round(adjusted_score, 2)


def calculate_composite_score(breakdown: ScoreBreakdown) -> float:
    """Calculate weighted composite score.

    Formula: 40% technical + 30% fundamental + 30% sentiment

    Args:
        breakdown: Individual score components

    Returns:
        Composite score between 0 and 100
    """
    composite = (
        breakdown.technical * TECHNICAL_WEIGHT +
        breakdown.fundamental * FUNDAMENTAL_WEIGHT +
        breakdown.sentiment * SENTIMENT_WEIGHT
    )
    return round(composite, 2)


def rank_and_allocate(scores: list[tuple[str, ScoreBreakdown]]) -> list[StockScore]:
    """Rank stocks and calculate allocation weights.

    Allocation uses score-weighted proportional allocation.

    Args:
        scores: List of (ticker, breakdown) tuples

    Returns:
        List of StockScore objects with rank and allocation
    """
    # Calculate composite scores
    stock_scores = []
    for ticker, breakdown in scores:
        composite = calculate_composite_score(breakdown)
        stock_scores.append((ticker, breakdown, composite))

    # Sort by composite score (highest first)
    stock_scores.sort(key=lambda x: x[2], reverse=True)

    # Calculate allocations proportional to scores
    total_score = sum(s[2] for s in stock_scores)

    results = []
    for rank, (ticker, breakdown, composite) in enumerate(stock_scores, 1):
        # Proportional allocation
        allocation = (
            (composite / total_score) * 100
            if total_score > 0
            else 100 / len(stock_scores)
        )

        results.append(
            StockScore(
                ticker=ticker,
                composite_score=composite,
                breakdown=breakdown,
                rank=rank,
                allocation_pct=round(allocation, 2),
            )
        )

    return results
