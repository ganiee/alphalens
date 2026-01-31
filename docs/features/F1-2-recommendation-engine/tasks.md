# F1-2: Recommendation Engine (Basic Scoring) - Tasks

## Phase A: Domain Layer

- [x] Create `domain/recommendation.py` with entities:
  - [x] `Horizon` enum (1W, 1M, 3M, 6M, 1Y)
  - [x] `StockTicker` validated model
  - [x] `RecommendationRequest` input model
  - [x] `TechnicalIndicators` model
  - [x] `FundamentalMetrics` model
  - [x] `SentimentData` model
  - [x] `StockScore` model with score breakdown
  - [x] `EvidencePacket` model
  - [x] `RecommendationResult` model
- [x] Create `domain/providers.py` with port interfaces:
  - [x] `MarketDataProvider` protocol
  - [x] `FundamentalsProvider` protocol
  - [x] `NewsProvider` protocol
  - [x] `SentimentAnalyzer` protocol

## Phase B: Mock Adapters

- [x] Create `adapters/mock_market_data.py`:
  - [x] Return fixed price history for test tickers
  - [x] Include OHLCV data for 200 days
- [x] Create `adapters/mock_fundamentals.py`:
  - [x] Return fixed P/E, margins, growth for test tickers
- [x] Create `adapters/mock_news.py`:
  - [x] Return fixed news articles for test tickers
- [x] Create `adapters/mock_sentiment.py`:
  - [x] Return fixed sentiment scores

## Phase C: Scoring Engine

- [x] Create `services/indicators.py`:
  - [x] RSI calculation
  - [x] MACD calculation
  - [x] SMA (50, 200) calculation
  - [x] Volume trend calculation
- [x] Create `services/scoring.py`:
  - [x] Technical score computation
  - [x] Fundamental score computation
  - [x] Sentiment score computation
  - [x] Composite score formula
- [x] Create `services/recommendation.py`:
  - [x] `RecommendationService` class
  - [x] Pipeline orchestration
  - [x] Plan validation (stocks per run, horizon access)
  - [x] Evidence packet assembly

## Phase D: API Endpoints

- [x] Create `routers/recommendations.py`:
  - [x] `POST /recommendations/analyze` endpoint
  - [x] `GET /recommendations/{run_id}` endpoint
  - [x] `GET /recommendations/` (history) endpoint
- [x] Update `routers/deps.py`:
  - [x] Add dependency injection for providers
  - [x] Add dependency for RecommendationService
- [x] Update `main.py`:
  - [x] Include recommendations router

## Phase E: In-Memory Storage (MVP)

- [x] Create `repo/recommendations.py`:
  - [x] In-memory storage for recommendation results
  - [x] Store/retrieve by run_id
  - [x] List runs by user_id
  - [x] Note: Persistent storage in future phase

## Phase F: Backend Tests

- [x] Create `tests/test_indicators.py`:
  - [x] Test RSI calculation with known values
  - [x] Test MACD calculation with known values
  - [x] Test SMA calculation with known values
- [x] Create `tests/test_scoring.py`:
  - [x] Test technical score formula
  - [x] Test fundamental score formula
  - [x] Test sentiment score formula
  - [x] Test composite score calculation
- [x] Create `tests/test_recommendation_service.py`:
  - [x] Test full pipeline with mocks
  - [x] Test plan validation (stock limits)
  - [x] Test horizon restrictions
- [x] Create `tests/test_recommendations_api.py`:
  - [x] Test analyze endpoint (success)
  - [x] Test analyze endpoint (auth required)
  - [x] Test analyze endpoint (plan limits)
  - [x] Test get result endpoint
  - [x] Test history endpoint

## Phase G: Frontend - Analyze Page

- [x] Create `app/analyze/page.tsx`:
  - [x] Ticker input component (inline)
  - [x] Horizon selector (plan-aware)
  - [x] Submit button with loading state
  - [x] Error handling display
- [x] Create `lib/api.ts`:
  - [x] API client for recommendations endpoints
  - [x] Token injection from auth context

## Phase H: Frontend - Results Page

- [x] Create `app/results/[runId]/page.tsx`:
  - [x] Fetch and display recommendation result
  - [x] Loading/error states
  - [x] ScoreCard component (inline)
  - [x] Score breakdown bars
  - [x] Allocation chart (horizontal bars)
  - [x] EvidenceSection component (collapsible)

## Phase I: Frontend - History Integration

- [x] Update `app/dashboard/page.tsx`:
  - [x] Add link to /analyze
  - [x] Add link to /history
- [x] Create `app/history/page.tsx`:
  - [x] List all user's past runs
  - [x] Click to view full result

## Phase J: Documentation & Cleanup

- [x] Update feature index to In Progress
- [x] Verify all tests pass (95 tests)
- [x] Verify lint passes
- [ ] Update acceptance.md checkboxes
- [ ] Final code review

## Pending (Future Phases)

- [ ] Real market data provider integration
- [ ] DynamoDB storage for runs
- [ ] Run limit enforcement (F1-3)
- [ ] LLM explanations (F1-4)
