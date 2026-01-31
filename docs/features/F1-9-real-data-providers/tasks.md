# F1-9: Real Data Providers - Tasks

## Phase A: Settings & Configuration

- [x] A1. Extend `backend/domain/settings.py` with API keys and cache config
- [x] A2. Update `backend/.env.example` with new environment variables

## Phase B: Caching Layer

- [x] B1. Create `backend/adapters/cache.py`
  - [x] CacheEntry model
  - [x] ProviderCache protocol
  - [x] SqliteProviderCache implementation
  - [x] NoOpCache for disabled caching
  - [x] make_cache_key helper function
- [x] B2. Create `backend/adapters/http_client.py`
  - [x] RetryingHttpClient with configurable timeout
  - [x] Exponential backoff retry logic

## Phase C: Real Data Providers

- [x] C1. Create `backend/adapters/polygon_market_data.py`
  - [x] Implement MarketDataProvider protocol
  - [x] Polygon API integration
  - [x] Cache integration
  - [x] Error handling with ProviderError
- [x] C2. Create `backend/adapters/fmp_fundamentals.py`
  - [x] Implement FundamentalsProvider protocol
  - [x] FMP API integration (profile, ratios-ttm, key-metrics-ttm)
  - [x] Cache integration
  - [x] Error handling
- [x] C3. Create `backend/adapters/newsapi_news.py`
  - [x] Implement NewsProvider protocol
  - [x] NewsAPI integration
  - [x] Simple sentiment labeling
  - [x] Cache integration

## Phase D: Domain Model Extensions

- [x] D1. Extend `backend/domain/providers.py`
  - [x] Add ProviderMetadata model
- [x] D2. Extend `backend/domain/recommendation.py`
  - [x] Add NewsArticleSummary model
  - [x] Add ProviderAttribution model
  - [x] Update EvidencePacket with news_articles and attribution

## Phase E: Dependency Injection

- [x] E1. Update `backend/routers/deps.py`
  - [x] Add get_provider_cache()
  - [x] Add get_http_client()
  - [x] Update get_recommendation_service() for conditional providers

## Phase F: Service Layer Updates

- [x] F1. Update `backend/services/recommendation.py`
  - [x] Add fallback logic (try real, catch error, use mock)
  - [x] Populate ProviderAttribution
  - [x] Populate news_articles in EvidencePacket

## Phase G: Frontend Updates

- [x] G1. Extend `frontend/lib/api.ts`
  - [x] Add NewsArticleSummary interface
  - [x] Add ProviderAttribution interface
  - [x] Update EvidencePacket interface
- [x] G2. Update `frontend/app/results/[runId]/page.tsx`
  - [x] Add ProviderBadge component
  - [x] Add timeAgo helper
  - [x] Add TechnicalPanel component
  - [x] Add FundamentalsPanel component
  - [x] Add SentimentPanel component
  - [x] Add NewsPanel component

## Phase H: Tests

- [x] H1. Create `backend/tests/test_cache.py`
  - [x] Test set/get operations
  - [x] Test TTL expiration
  - [x] Test cache miss returns None
  - [x] Test clear_expired
- [x] H2. Create `backend/tests/test_polygon_provider.py`
  - [x] Test successful fetch
  - [x] Test cached data return
  - [x] Test API error handling
  - [x] Test HTTP error handling
- [x] H3. Create `backend/tests/test_fmp_provider.py`
  - [x] Test successful fetch
  - [x] Test fundamentals mapping
  - [x] Test null value handling
  - [x] Test API error handling
- [x] H4. Create `backend/tests/test_newsapi_provider.py`
  - [x] Test news article parsing
  - [x] Test sentiment labeling (positive/negative/neutral)
  - [x] Test cached data return
  - [x] Test API error handling
- [x] H5. Update `backend/tests/test_recommendation_service.py`
  - [x] Test attribution populated correctly
  - [x] Test news_articles in evidence
  - [x] Test attribution timestamps

## Phase I: Documentation

- [x] I1. Create feature docs in `docs/features/F1-9-real-data-providers/`
  - [x] spec.md
  - [x] tasks.md
  - [x] tests.md
  - [x] acceptance.md
  - [x] rollback.md
- [x] I2. Update `docs/feature.index.md`
