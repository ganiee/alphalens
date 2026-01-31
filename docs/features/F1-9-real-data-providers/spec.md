# F1-9: Real Data Providers + Caching + UI Display - Specification

## Overview

This feature replaces mock data providers with real external APIs and adds a caching layer for performance optimization. It also enhances the UI to display provider attribution and data freshness information.

**Key Principles:**
- Real data from Polygon.io, Financial Modeling Prep (FMP), and NewsAPI
- Automatic fallback to mock providers when APIs unavailable
- SQLite-based caching with configurable TTL
- Provider attribution displayed in UI

## Architecture

### Data Providers

| Provider | Data Type | Endpoint | Cache TTL |
|----------|-----------|----------|-----------|
| Polygon.io | Market prices (OHLCV) | `/v2/aggs/ticker/{ticker}/range/1/day/{from}/{to}` | 60 seconds |
| FMP | Fundamentals | `/profile`, `/ratios-ttm`, `/key-metrics-ttm` | 24 hours |
| NewsAPI | News articles | `/v2/everything` | 5 minutes |

### Caching Layer

**SQLite Cache Schema:**
```sql
CREATE TABLE cache_entries (
    cache_key TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    data TEXT NOT NULL,
    ticker TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
```

**Cache Key Format:**
- `{provider}:{operation}:{ticker}:{param}={value}`
- Example: `polygon:price_history:AAPL:days=200`

### Fallback Strategy

1. Attempt real provider fetch
2. On `ProviderError`, log warning and fall back to mock
3. Mock provider always returns deterministic data
4. Attribution reflects actual provider used

## Backend Implementation

### New Files

| File | Purpose |
|------|---------|
| `adapters/cache.py` | CacheEntry model, ProviderCache protocol, SqliteProviderCache |
| `adapters/http_client.py` | RetryingHttpClient with timeout and backoff |
| `adapters/polygon_market_data.py` | Polygon.io market data provider |
| `adapters/fmp_fundamentals.py` | FMP fundamentals provider |
| `adapters/newsapi_news.py` | NewsAPI news provider |

### Modified Files

| File | Changes |
|------|---------|
| `domain/settings.py` | Add API keys, cache config, HTTP settings |
| `domain/providers.py` | Add ProviderMetadata model |
| `domain/recommendation.py` | Add NewsArticleSummary, ProviderAttribution, update EvidencePacket |
| `routers/deps.py` | Add cache/HTTP client dependencies, conditional provider selection |
| `services/recommendation.py` | Add fallback logic, populate attribution |

### Configuration

```python
# API Keys
fmp_api_key: str = ""
polygon_api_key: str = ""
news_api_key: str = ""

# Cache
provider_cache_enabled: bool = True
provider_cache_backend: str = "sqlite"
provider_cache_db_path: str = ".cache/alphalens/cache.sqlite"
market_cache_ttl_seconds: int = 60
fundamentals_cache_ttl_seconds: int = 86400
news_cache_ttl_seconds: int = 300

# HTTP Client
http_timeout_seconds: int = 10
http_max_retries: int = 2
http_retry_backoff_seconds: float = 0.5
```

## Frontend Implementation

### New Components

| Component | Purpose |
|-----------|---------|
| `ProviderBadge` | Colored badge showing provider name (Polygon, FMP, NewsAPI, mock) |
| `timeAgo()` | Helper to format timestamps as "5 min ago" |
| `TechnicalPanel` | Technical indicators with provider badge |
| `FundamentalsPanel` | Fundamentals with provider badge |
| `NewsPanel` | News articles with title, source, sentiment label, link |
| `SentimentPanel` | Sentiment analysis data |

### New TypeScript Interfaces

```typescript
interface NewsArticleSummary {
  title: string;
  source: string;
  published_at: string;
  url: string;
  sentiment_label: string | null;
}

interface ProviderAttribution {
  market_data_provider: string;
  market_data_fetched_at: string | null;
  fundamentals_provider: string;
  fundamentals_fetched_at: string | null;
  news_provider: string;
  news_fetched_at: string | null;
}
```

## Data Flow

```
User requests analysis
  → RecommendationService.run()
    → For each ticker:
      → Attempt Polygon fetch (with cache check)
        → On fail: fallback to MockMarketDataProvider
      → Attempt FMP fetch (with cache check)
        → On fail: fallback to MockFundamentalsProvider
      → Attempt NewsAPI fetch (with cache check)
        → On fail: fallback to MockNewsProvider
      → Compute technical indicators
      → Analyze sentiment
      → Build EvidencePacket with attribution
    → Score, rank, allocate
    → Return RecommendationResult
  → Frontend displays results with provider badges
```

## Security Considerations

- API keys stored in environment variables
- Keys never exposed to frontend
- HTTP client validates SSL certificates
- Cache stored locally (not shared)

## Testing Strategy

- All provider tests use mocked HTTP responses
- No live API calls in tests
- Cache tests use temporary SQLite databases
- Fallback logic tested with simulated failures

## Rollback Plan

1. Set API keys to empty strings in environment
2. System automatically falls back to mock providers
3. No database migrations to reverse
4. Cache directory can be deleted: `rm -rf .cache/alphalens`

## Dependencies

### Backend
- `httpx` - Async HTTP client (already present)
- SQLite3 - Python standard library (no new deps)

### Frontend
- No new dependencies

## Out of Scope

- Persistent storage of provider responses beyond cache TTL
- Provider health monitoring dashboard
- API usage metering/billing
- Rate limiting per provider
- Multiple cache backends (Redis, Memcached)
