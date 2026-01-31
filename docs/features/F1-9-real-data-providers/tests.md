# F1-9: Real Data Providers - Tests

## Unit Tests

### Cache Layer (`test_cache.py`)

| Test | Description |
|------|-------------|
| `test_basic_key` | Cache key generation with basic params |
| `test_key_with_params` | Cache key with additional parameters |
| `test_key_with_multiple_params` | Cache key params are sorted |
| `test_get_returns_none` | NoOpCache.get returns None |
| `test_set_does_nothing` | NoOpCache.set completes without error |
| `test_delete_does_nothing` | NoOpCache.delete completes without error |
| `test_clear_expired_returns_zero` | NoOpCache.clear_expired returns 0 |
| `test_set_and_get` | SqliteCache stores and retrieves entries |
| `test_get_miss_returns_none` | SqliteCache returns None for missing key |
| `test_get_expired_returns_none` | SqliteCache returns None for expired entry |
| `test_delete` | SqliteCache deletes entry |
| `test_clear_expired` | SqliteCache removes expired entries |
| `test_overwrite_existing` | SqliteCache overwrites on duplicate key |
| `test_creates_cache_directory` | Cache creates parent directories |
| `test_complex_data_serialization` | Cache handles nested data structures |

### Polygon Provider (`test_polygon_provider.py`)

| Test | Description |
|------|-------------|
| `test_successful_fetch` | Fetches and parses price history correctly |
| `test_returns_cached_data` | Returns cached data without API call |
| `test_api_error_response` | Handles API error response |
| `test_empty_results` | Handles empty results |
| `test_http_error` | Handles HTTP connection errors |
| `test_price_history_properties` | PriceHistory has correct properties |

### FMP Provider (`test_fmp_provider.py`)

| Test | Description |
|------|-------------|
| `test_successful_fetch` | Combines data from multiple endpoints |
| `test_returns_cached_data` | Returns cached data without API call |
| `test_handles_null_values` | Handles null/missing values gracefully |
| `test_api_error_response` | Handles API error response |
| `test_http_error` | Handles HTTP connection errors |
| `test_empty_response_list` | Handles empty response lists |
| `test_cache_key_format` | Uses correct cache key format |

### NewsAPI Provider (`test_newsapi_provider.py`)

| Test | Description |
|------|-------------|
| `test_successful_fetch` | Fetches and parses news articles |
| `test_sentiment_label_positive` | Labels positive news correctly |
| `test_sentiment_label_negative` | Labels negative news correctly |
| `test_sentiment_label_neutral` | Labels neutral news correctly |
| `test_returns_cached_data` | Returns cached data without API call |
| `test_api_error_response` | Handles API error response |
| `test_http_error` | Handles HTTP connection errors |
| `test_empty_articles` | Handles empty article list |
| `test_max_articles_limit` | Respects max_articles limit |
| `test_missing_source_name` | Handles missing source name |

### Recommendation Service (`test_recommendation_service.py`)

| Test | Description |
|------|-------------|
| `test_evidence_has_attribution` | Evidence includes provider attribution |
| `test_evidence_has_news_articles` | Evidence includes news article summaries |
| `test_attribution_timestamps_populated` | Attribution timestamps are set |

## Integration Tests

Integration tests verify the full pipeline works with mock providers:

```bash
cd backend && AUTH_MODE=mock pytest -v
```

## Manual Testing

### Mock Provider Mode (No API Keys)

1. Start backend without API keys:
   ```bash
   cd backend && uvicorn main:app --reload
   ```

2. Start frontend:
   ```bash
   cd frontend && npm run dev
   ```

3. Log in and analyze stocks
4. Verify:
   - Results display correctly
   - Provider badges show "mock"
   - No errors in console

### Real Provider Mode (With API Keys)

1. Set API keys in `.env`:
   ```
   POLYGON_API_KEY=your_key
   FMP_API_KEY=your_key
   NEWS_API_KEY=your_key
   ```

2. Start services and analyze stocks
3. Verify:
   - Provider badges show "Polygon", "FMP", "NewsAPI"
   - Data appears realistic
   - Timestamps show recent fetch times

### Cache Verification

1. Make a request and note response time
2. Make the same request again
3. Verify:
   - Second request is faster
   - `.cache/alphalens/cache.sqlite` exists
   - Cache entries visible in SQLite browser

### Fallback Testing

1. Set invalid API key for one provider
2. Make a request
3. Verify:
   - Request succeeds (uses mock fallback)
   - Warning logged about fallback
   - Provider badge shows "mock" for failed provider

## Running Tests

```bash
# All backend tests
cd backend && AUTH_MODE=mock pytest -v

# Cache tests only
cd backend && pytest -v tests/test_cache.py

# Provider tests only
cd backend && pytest -v tests/test_polygon_provider.py tests/test_fmp_provider.py tests/test_newsapi_provider.py

# Recommendation service tests
cd backend && pytest -v tests/test_recommendation_service.py
```
