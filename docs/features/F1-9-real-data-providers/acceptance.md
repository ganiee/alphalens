# F1-9: Real Data Providers - Acceptance Criteria

## Functional Requirements

### FR1: Real Data Provider Integration

- [ ] **FR1.1**: When `POLYGON_API_KEY` is set, market data is fetched from Polygon.io
- [ ] **FR1.2**: When `FMP_API_KEY` is set, fundamentals are fetched from Financial Modeling Prep
- [ ] **FR1.3**: When `NEWS_API_KEY` is set, news articles are fetched from NewsAPI
- [ ] **FR1.4**: When API keys are not set, corresponding mock providers are used

### FR2: Automatic Fallback

- [ ] **FR2.1**: On provider API error, system falls back to mock provider
- [ ] **FR2.2**: On provider timeout, system falls back to mock provider
- [ ] **FR2.3**: Fallback is logged for debugging
- [ ] **FR2.4**: Fallback does not cause request failure

### FR3: Response Caching

- [ ] **FR3.1**: Market data responses are cached for 60 seconds (configurable)
- [ ] **FR3.2**: Fundamentals responses are cached for 24 hours (configurable)
- [ ] **FR3.3**: News responses are cached for 5 minutes (configurable)
- [ ] **FR3.4**: Cache is SQLite-based and persists across restarts
- [ ] **FR3.5**: Expired cache entries are not returned
- [ ] **FR3.6**: Cache can be disabled via `PROVIDER_CACHE_ENABLED=false`

### FR4: Provider Attribution

- [ ] **FR4.1**: EvidencePacket includes `attribution` with provider names
- [ ] **FR4.2**: EvidencePacket includes `news_articles` list
- [ ] **FR4.3**: Attribution includes `fetched_at` timestamps

### FR5: UI Display

- [ ] **FR5.1**: Provider badges display provider name (Polygon, FMP, NewsAPI, mock)
- [ ] **FR5.2**: Provider badges are color-coded by provider
- [ ] **FR5.3**: Data freshness shown as relative time ("5 min ago")
- [ ] **FR5.4**: News articles display title, source, time, and link
- [ ] **FR5.5**: News articles show sentiment label (positive/negative/neutral)

## Non-Functional Requirements

### NFR1: Performance

- [ ] **NFR1.1**: Cached requests complete in < 100ms
- [ ] **NFR1.2**: Non-cached requests complete in < 5 seconds
- [ ] **NFR1.3**: HTTP timeout is configurable (default 10s)

### NFR2: Reliability

- [ ] **NFR2.1**: System functions with partial provider availability
- [ ] **NFR2.2**: HTTP client retries failed requests (configurable)
- [ ] **NFR2.3**: Exponential backoff between retries

### NFR3: Security

- [ ] **NFR3.1**: API keys stored only in environment variables
- [ ] **NFR3.2**: API keys never exposed to frontend
- [ ] **NFR3.3**: Cache stored in local filesystem only

### NFR4: Maintainability

- [ ] **NFR4.1**: All new code has unit tests
- [ ] **NFR4.2**: Provider implementations follow existing protocols
- [ ] **NFR4.3**: Configuration documented in `.env.example`

## Verification Steps

### V1: Backend Tests Pass

```bash
cd backend && AUTH_MODE=mock pytest -v
```

Expected: All tests pass, including new cache and provider tests.

### V2: Manual Test - Mock Mode

1. Ensure no API keys are set
2. Start backend and frontend
3. Analyze stocks (e.g., AAPL, MSFT)
4. Expected:
   - Results display correctly
   - Provider badges show "mock"
   - No errors in logs

### V3: Manual Test - Real Mode

1. Set API keys in `.env`:
   ```
   POLYGON_API_KEY=your_key
   FMP_API_KEY=your_key
   NEWS_API_KEY=your_key
   ```
2. Start backend and frontend
3. Analyze stocks
4. Expected:
   - Results display with real data
   - Provider badges show "Polygon", "FMP", "NewsAPI"
   - News articles have clickable links
   - Timestamps show recent times

### V4: Cache Verification

1. Analyze a stock
2. Check `.cache/alphalens/cache.sqlite` exists
3. Analyze same stock again
4. Expected: Second request noticeably faster

### V5: Fallback Verification

1. Set one API key to invalid value
2. Analyze stocks
3. Expected:
   - Request succeeds
   - Affected provider shows "mock"
   - Warning in logs about fallback

## Sign-Off

| Criterion | Status | Verified By | Date |
|-----------|--------|-------------|------|
| FR1: Real providers | | | |
| FR2: Fallback | | | |
| FR3: Caching | | | |
| FR4: Attribution | | | |
| FR5: UI Display | | | |
| NFR1: Performance | | | |
| NFR2: Reliability | | | |
| NFR3: Security | | | |
| NFR4: Maintainability | | | |
| V1: Tests pass | | | |
| V2: Mock mode | | | |
| V3: Real mode | | | |
| V4: Cache | | | |
| V5: Fallback | | | |
