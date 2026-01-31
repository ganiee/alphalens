"""Domain entities for stock recommendations."""

import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from domain.auth import UserPlan


class Horizon(str, Enum):
    """Investment time horizons."""

    ONE_WEEK = "1W"
    ONE_MONTH = "1M"
    THREE_MONTHS = "3M"
    SIX_MONTHS = "6M"
    ONE_YEAR = "1Y"


# Horizons available for free plan
FREE_PLAN_HORIZONS = {Horizon.ONE_MONTH}

# All horizons available for pro plan
PRO_PLAN_HORIZONS = set(Horizon)


class StockTicker(BaseModel):
    """Validated stock ticker symbol."""

    symbol: Annotated[str, Field(min_length=1, max_length=10)]

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate ticker symbol format."""
        v = v.upper().strip()
        if not re.match(r"^[A-Z]{1,5}$", v):
            raise ValueError(f"Invalid ticker symbol: {v}. Must be 1-5 uppercase letters.")
        return v


class TechnicalIndicators(BaseModel):
    """Technical analysis indicators for a stock."""

    rsi: float = Field(ge=0, le=100, description="Relative Strength Index")
    macd: float = Field(description="MACD line value")
    macd_signal: float = Field(description="MACD signal line value")
    macd_histogram: float = Field(description="MACD histogram value")
    sma_50: float = Field(description="50-day Simple Moving Average")
    sma_200: float = Field(description="200-day Simple Moving Average")
    current_price: float = Field(gt=0, description="Current stock price")
    volume_trend: float = Field(description="Volume trend: >1 increasing, <1 decreasing")


class FundamentalMetrics(BaseModel):
    """Fundamental analysis metrics for a stock."""

    pe_ratio: float | None = Field(default=None, description="Price-to-Earnings ratio")
    revenue_growth: float | None = Field(default=None, description="Year-over-year revenue growth")
    profit_margin: float | None = Field(default=None, ge=0, le=1, description="Net profit margin")
    debt_to_equity: float | None = Field(default=None, ge=0, description="Debt-to-Equity ratio")
    market_cap: float | None = Field(default=None, gt=0, description="Market cap in USD")


class SentimentData(BaseModel):
    """News sentiment data for a stock."""

    score: float = Field(ge=-1, le=1, description="Sentiment score: -1 to 1")
    article_count: int = Field(ge=0, description="Number of articles analyzed")
    positive_count: int = Field(ge=0, description="Number of positive articles")
    negative_count: int = Field(ge=0, description="Number of negative articles")
    neutral_count: int = Field(ge=0, description="Number of neutral articles")


class ScoreBreakdown(BaseModel):
    """Breakdown of individual score components."""

    technical: float = Field(ge=0, le=100, description="Technical analysis score")
    fundamental: float = Field(ge=0, le=100, description="Fundamental analysis score")
    sentiment: float = Field(ge=0, le=100, description="Sentiment analysis score")


class StockScore(BaseModel):
    """Score result for a single stock."""

    ticker: str
    composite_score: float = Field(ge=0, le=100, description="Overall composite score")
    breakdown: ScoreBreakdown
    rank: int = Field(ge=1, description="Rank among analyzed stocks")
    allocation_pct: float = Field(ge=0, le=100, description="Recommended allocation percentage")


class EvidencePacket(BaseModel):
    """Raw evidence data used for scoring (stored per run)."""

    ticker: str
    technical: TechnicalIndicators
    fundamental: FundamentalMetrics
    sentiment: SentimentData
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class RecommendationRequest(BaseModel):
    """Input request for a recommendation run."""

    tickers: list[str] = Field(min_length=1, description="List of ticker symbols")
    horizon: Horizon = Field(default=Horizon.ONE_MONTH, description="Investment horizon")

    @field_validator("tickers")
    @classmethod
    def validate_tickers(cls, v: list[str]) -> list[str]:
        """Validate and normalize ticker symbols."""
        validated = []
        for ticker in v:
            ticker = ticker.upper().strip()
            if not re.match(r"^[A-Z]{1,5}$", ticker):
                raise ValueError(f"Invalid ticker symbol: {ticker}. Must be 1-5 uppercase letters.")
            if ticker not in validated:  # Remove duplicates
                validated.append(ticker)
        return validated


class RecommendationResult(BaseModel):
    """Output result from a recommendation run."""

    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    tickers: list[str]
    horizon: Horizon
    scores: list[StockScore]
    evidence: list[EvidencePacket]
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def total_allocation(self) -> float:
        """Sum of all allocation percentages (should be 100)."""
        return sum(s.allocation_pct for s in self.scores)


class RecommendationSummary(BaseModel):
    """Summary of a recommendation run (for history listing)."""

    run_id: str
    tickers: list[str]
    horizon: Horizon
    top_pick: str | None = None
    top_score: float | None = None
    created_at: datetime


# Plan constraints
PLAN_CONSTRAINTS = {
    UserPlan.FREE: {
        "max_tickers": 3,
        "allowed_horizons": FREE_PLAN_HORIZONS,
    },
    UserPlan.PRO: {
        "max_tickers": 5,
        "allowed_horizons": PRO_PLAN_HORIZONS,
    },
}


class PlanConstraintError(Exception):
    """Raised when a request violates plan constraints."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def validate_request_for_plan(request: RecommendationRequest, plan: UserPlan) -> None:
    """Validate that a request meets plan constraints.

    Args:
        request: The recommendation request
        plan: User's subscription plan

    Raises:
        PlanConstraintError: If request violates plan limits
    """
    constraints = PLAN_CONSTRAINTS[plan]

    # Check ticker count
    if len(request.tickers) > constraints["max_tickers"]:
        raise PlanConstraintError(
            f"{plan.value.capitalize()} plan allows maximum {constraints['max_tickers']} "
            f"tickers per run. You requested {len(request.tickers)}."
        )

    # Check horizon access
    if request.horizon not in constraints["allowed_horizons"]:
        allowed = ", ".join(h.value for h in constraints["allowed_horizons"])
        raise PlanConstraintError(
            f"{plan.value.capitalize()} plan only allows these horizons: {allowed}. "
            f"Upgrade to Pro for access to {request.horizon.value}."
        )
