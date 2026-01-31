# F1-9: Real Data Providers - Rollback Plan

## Overview

F1-9 is designed with automatic fallback, making rollback straightforward. The system defaults to mock providers when API keys are absent.

## Rollback Scenarios

### Scenario 1: Disable Real Providers (Keep Changes)

**Impact**: System reverts to mock providers while code changes remain.

**Steps**:
1. Remove or clear API keys from environment:
   ```bash
   # In .env or environment
   POLYGON_API_KEY=
   FMP_API_KEY=
   NEWS_API_KEY=
   ```

2. Restart backend:
   ```bash
   # Docker
   docker-compose restart backend

   # Local
   # Kill and restart uvicorn
   ```

3. Verify mock providers active:
   - Analyze stocks
   - Provider badges should show "mock"

**Rollback Time**: < 5 minutes

### Scenario 2: Disable Caching Only

**Impact**: Providers still work, but without caching.

**Steps**:
1. Set cache disabled:
   ```bash
   PROVIDER_CACHE_ENABLED=false
   ```

2. Optionally clear existing cache:
   ```bash
   rm -rf .cache/alphalens
   ```

3. Restart backend

**Rollback Time**: < 5 minutes

### Scenario 3: Full Code Rollback

**Impact**: Revert all F1-9 code changes.

**Steps**:
1. Identify last good commit before F1-9:
   ```bash
   git log --oneline
   ```

2. Revert or reset:
   ```bash
   # If F1-9 is a single commit
   git revert <commit-hash>

   # If multiple commits, reset to pre-F1-9
   git reset --hard <pre-f1-9-commit>
   ```

3. Clear cache directory:
   ```bash
   rm -rf .cache/alphalens
   ```

4. Restart services:
   ```bash
   docker-compose down && docker-compose up -d
   ```

**Rollback Time**: 15-30 minutes

## No Database Migrations

F1-9 does not add database migrations. The SQLite cache is:
- Ephemeral (can be deleted)
- Local to each instance
- Not part of application state

## Files Changed

### New Files (Delete on Full Rollback)
```
backend/adapters/cache.py
backend/adapters/http_client.py
backend/adapters/polygon_market_data.py
backend/adapters/fmp_fundamentals.py
backend/adapters/newsapi_news.py
backend/tests/test_cache.py
backend/tests/test_polygon_provider.py
backend/tests/test_fmp_provider.py
backend/tests/test_newsapi_provider.py
docs/features/F1-9-real-data-providers/
```

### Modified Files (Revert Changes)
```
backend/domain/settings.py
backend/domain/providers.py
backend/domain/recommendation.py
backend/routers/deps.py
backend/services/recommendation.py
backend/.env.example
frontend/lib/api.ts
frontend/app/results/[runId]/page.tsx
docs/feature.index.md
```

## Verification After Rollback

1. **Tests Pass**:
   ```bash
   cd backend && AUTH_MODE=mock pytest -v
   ```

2. **Manual Verification**:
   - Login and analyze stocks
   - Results display correctly
   - No errors in logs

3. **Cache Cleaned**:
   ```bash
   ls .cache/alphalens  # Should not exist or be empty
   ```

## Emergency Contact

If rollback fails:
1. Check logs for specific errors
2. Ensure all API keys cleared
3. Verify database connection (not affected by F1-9)
4. Contact team lead

## Monitoring

After rollback, monitor:
- Application health endpoint: `/health`
- Error rates in logs
- User complaints about data freshness (expected with mock)
