# F1-2: Recommendation Engine (Basic Scoring) - Specification

## Overview

This feature implements the core recommendation engine that:
- Accepts stock tickers and investment horizon as input
- Fetches market data, fundamentals, and news
- Computes technical indicators and sentiment scores
- Applies deterministic scoring algorithm
- Ranks stocks and generates allocation weights
- Returns structured recommendation with evidence packet

**Key Principle**: LLMs summarize evidence, they do NOT make decisions. All scoring is deterministic.

## Architecture

### Backend (FastAPI)

**Ports (Interfaces in `domain/`):**
- `MarketDataProvider` - Fetches price history and volume
- `FundamentalsProvider` - Fetches financial ratios, earnings
- `NewsProvider` - Fetches recent news articles
- `SentimentAnalyzer` - Analyzes sentiment from text
- `RecommendationEngine` - Orchestrates the scoring pipeline

**Adapters (Implementations in `adapters/`):**
- `MockMarketDataProvider` - Test data for development
- `MockFundamentalsProvider` - Test data for development
- `MockNewsProvider` - Test data for development
- `MockSentimentAnalyzer` - Returns fixed sentiment scores
- `BasicRecommendationEngine` - Implements scoring algorithm

**Domain Entities (`domain/recommendation.py`):**
- `StockTicker` - Validated stock symbol
- `Horizon` - Enum: 1W, 1M, 3M, 6M, 1Y
- `RecommendationRequest` - Input: tickers, horizon, user plan
- `StockScore` - Individual stock score with breakdown
- `RecommendationResult` - Output: ranked stocks, allocations, evidence
- `EvidencePacket` - Raw data used for scoring (stored per run)

**Services (`services/recommendation.py`):**
- `RecommendationService` - Use case orchestration
  - Validates user limits
  - Executes pipeline
  - Stores evidence
  - Returns result

### Pipeline Steps

Following the base PRD contract:
```
FetchData → ComputeFeatures → Score → Rank → Allocate → Explain
```

1. **FetchData**: Fetch price history, fundamentals, news for each ticker
2. **ComputeFeatures**: Calculate technical indicators (RSI, MACD, SMA, etc.)
3. **Score**: Apply deterministic scoring formula
4. **Rank**: Sort stocks by composite score
5. **Allocate**: Generate portfolio weights (equal weight for MVP)
6. **Explain**: Package evidence for LLM summarization (F1-4)

### Scoring Algorithm (MVP)

```
composite_score = (
    technical_score * 0.40 +
    fundamental_score * 0.30 +
    sentiment_score * 0.30
)
```

**Technical Score (0-100):**
- RSI position (oversold=high, overbought=low)
- MACD signal (bullish crossover=high)
- Price vs SMA50/SMA200 (above=bullish)
- Volume trend

**Fundamental Score (0-100):**
- P/E ratio vs sector average
- Revenue growth
- Profit margin
- Debt/Equity ratio

**Sentiment Score (0-100):**
- News sentiment (positive/negative/neutral)
- News volume/recency

### API Endpoints

**POST /recommendations/analyze**
- Auth: Required
- Body: `{ "tickers": ["AAPL", "MSFT"], "horizon": "1M" }`
- Response: `RecommendationResult`
- Enforces plan limits (stock count, horizon access)

**GET /recommendations/{run_id}**
- Auth: Required (owner only)
- Returns: Stored recommendation result

**GET /recommendations/history**
- Auth: Required
- Returns: List of user's past runs (summary only)

### Plan Enforcement

| Constraint | Free | Pro |
|------------|------|-----|
| Stocks per run | 3 max | 5 max |
| Primary horizon | 1M only | 1W/1M/3M/6M/1Y |
| Run limit | 3/month | 20/month |

Note: Run limit enforcement is F1-3 scope. This feature validates input constraints only.

## Frontend

**Pages:**
- `/analyze` - Run analysis form (ticker input, horizon selector)
- `/results/[run_id]` - Display recommendation results

**Components:**
- `TickerInput` - Multi-ticker input with validation
- `HorizonSelector` - Dropdown with plan-based restrictions
- `ScoreCard` - Display individual stock score
- `AllocationChart` - Visual allocation weights
- `EvidencePanel` - Collapsible raw evidence data

## Data Flow

```
User → /analyze page
  → Selects tickers + horizon
  → POST /recommendations/analyze
    → RecommendationService.run()
      → Fetch data (parallel)
      → Compute features
      → Score each stock
      → Rank & allocate
      → Store evidence + result
    → Return run_id + result
  → Redirect to /results/[run_id]
  → Display scores, allocations, evidence
```

## Security

- All endpoints require authentication (F1-1)
- Users can only view their own runs
- Input validation prevents injection
- Rate limiting (future: F1-3)

## Configuration

Environment variables:
- `RECOMMENDATION_CACHE_TTL` - Data cache TTL in seconds (default: 3600)

## Dependencies

### Backend
- `numpy` - Numerical computations
- `pandas` - Data manipulation (optional, may use pure Python)

### Frontend
- Chart library (for allocation visualization)

## Testing Strategy

- All providers mocked with fixed fixtures
- Deterministic test data (no live market data)
- Scoring algorithm unit tested with known inputs/outputs
- Integration tests verify full pipeline
- No flaky tests (frozen time, fixed data)

## Out of Scope (F1-2)

- LLM explanations (F1-4)
- Run limit enforcement (F1-3)
- Real market data providers (future phase)
- Caching layer (data freshness - partial, basic only)
- Historical backtesting

## Infrastructure

No new AWS infrastructure required for F1-2. All data providers are mocked.

Future phases will add:
- DynamoDB for storing runs/evidence
- External API integrations (market data vendors)
