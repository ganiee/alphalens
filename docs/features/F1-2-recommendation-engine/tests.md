# F1-2: Recommendation Engine (Basic Scoring) - Tests

## Test File Locations

- `backend/tests/test_indicators.py` - Technical indicator calculations
- `backend/tests/test_scoring.py` - Scoring algorithm tests
- `backend/tests/test_recommendation_service.py` - Service layer tests
- `backend/tests/test_recommendations_api.py` - API endpoint tests

## Test Coverage

### Technical Indicators (`test_indicators.py`)

| Test | Description |
|------|-------------|
| `test_rsi_oversold` | RSI < 30 indicates oversold |
| `test_rsi_overbought` | RSI > 70 indicates overbought |
| `test_rsi_neutral` | RSI 30-70 indicates neutral |
| `test_rsi_known_values` | RSI matches expected for known price series |
| `test_macd_bullish_crossover` | MACD line crosses above signal |
| `test_macd_bearish_crossover` | MACD line crosses below signal |
| `test_macd_histogram` | Histogram = MACD - Signal |
| `test_sma_50_calculation` | SMA50 computed correctly |
| `test_sma_200_calculation` | SMA200 computed correctly |
| `test_price_above_sma` | Detects price > SMA |
| `test_price_below_sma` | Detects price < SMA |
| `test_volume_trend_increasing` | Detects increasing volume |
| `test_volume_trend_decreasing` | Detects decreasing volume |

### Scoring Algorithm (`test_scoring.py`)

| Test | Description |
|------|-------------|
| `test_technical_score_range` | Score between 0-100 |
| `test_technical_score_bullish` | High score for bullish indicators |
| `test_technical_score_bearish` | Low score for bearish indicators |
| `test_fundamental_score_range` | Score between 0-100 |
| `test_fundamental_score_strong` | High score for strong fundamentals |
| `test_fundamental_score_weak` | Low score for weak fundamentals |
| `test_sentiment_score_range` | Score between 0-100 |
| `test_sentiment_score_positive` | High score for positive news |
| `test_sentiment_score_negative` | Low score for negative news |
| `test_composite_score_formula` | Verifies 40/30/30 weighting |
| `test_composite_score_range` | Composite between 0-100 |

### Recommendation Service (`test_recommendation_service.py`)

| Test | Description |
|------|-------------|
| `test_pipeline_execution` | Full pipeline runs without error |
| `test_pipeline_returns_result` | Returns RecommendationResult |
| `test_result_has_scores` | Each ticker has score |
| `test_result_has_allocations` | Allocations sum to 100% |
| `test_result_has_evidence` | Evidence packet included |
| `test_stocks_ranked_by_score` | Higher scores first |
| `test_free_plan_max_3_stocks` | Rejects > 3 tickers for free |
| `test_pro_plan_max_5_stocks` | Allows up to 5 tickers for pro |
| `test_free_plan_horizon_1m_only` | Free limited to 1M horizon |
| `test_pro_plan_all_horizons` | Pro can use any horizon |
| `test_evidence_contains_indicators` | Evidence has tech indicators |
| `test_evidence_contains_fundamentals` | Evidence has fundamental data |
| `test_evidence_contains_sentiment` | Evidence has sentiment data |

### API Endpoints (`test_recommendations_api.py`)

| Test | Endpoint | Description |
|------|----------|-------------|
| `test_analyze_requires_auth` | POST /analyze | Returns 401 without token |
| `test_analyze_with_valid_token` | POST /analyze | Returns result with auth |
| `test_analyze_invalid_ticker` | POST /analyze | Returns 400 for bad ticker |
| `test_analyze_too_many_tickers_free` | POST /analyze | Returns 400 for >3 tickers |
| `test_analyze_max_tickers_pro` | POST /analyze | Allows 5 tickers for pro |
| `test_analyze_invalid_horizon_free` | POST /analyze | Returns 400 for non-1M |
| `test_analyze_valid_horizon_pro` | POST /analyze | Allows any horizon for pro |
| `test_analyze_returns_run_id` | POST /analyze | Response includes run_id |
| `test_get_result_requires_auth` | GET /{run_id} | Returns 401 without token |
| `test_get_result_not_found` | GET /{run_id} | Returns 404 for bad id |
| `test_get_result_wrong_user` | GET /{run_id} | Returns 403 for other user |
| `test_get_result_success` | GET /{run_id} | Returns result for owner |
| `test_history_requires_auth` | GET /history | Returns 401 without token |
| `test_history_empty_new_user` | GET /history | Returns [] for new user |
| `test_history_lists_runs` | GET /history | Returns user's runs |

## Test Fixtures

### Mock Market Data
```python
MOCK_PRICE_DATA = {
    "AAPL": {
        "prices": [150.0, 151.5, 149.0, 152.0, ...],  # 90 days
        "volumes": [1000000, 1100000, ...],
        "dates": ["2024-01-01", "2024-01-02", ...]
    },
    "MSFT": { ... },
    "GOOGL": { ... }
}
```

### Mock Fundamentals
```python
MOCK_FUNDAMENTALS = {
    "AAPL": {
        "pe_ratio": 25.5,
        "revenue_growth": 0.08,
        "profit_margin": 0.25,
        "debt_equity": 1.5
    },
    ...
}
```

### Mock News/Sentiment
```python
MOCK_SENTIMENT = {
    "AAPL": {"score": 0.7, "article_count": 15},
    "MSFT": {"score": 0.5, "article_count": 10},
    ...
}
```

## Running Tests

```bash
# All F1-2 tests
cd backend
AUTH_MODE=mock pytest tests/test_indicators.py tests/test_scoring.py tests/test_recommendation_service.py tests/test_recommendations_api.py -v

# Individual test files
pytest tests/test_indicators.py -v
pytest tests/test_scoring.py -v
pytest tests/test_recommendation_service.py -v
pytest tests/test_recommendations_api.py -v

# With coverage
pytest tests/test_*.py --cov=services --cov=domain --cov-report=term-missing
```

## Test Strategy

- **Mock Providers**: All external data providers are mocked
- **Deterministic**: Fixed test data with known expected outputs
- **No Network**: Zero external API calls in tests
- **Fast**: All tests run in-memory
- **Isolated**: Each test independent, no shared state
- **Frozen Time**: Use fixed timestamps for reproducibility
