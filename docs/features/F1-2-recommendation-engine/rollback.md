# F1-2: Recommendation Engine (Basic Scoring) - Rollback Plan

## Overview

This document describes how to rollback F1-2 recommendation engine changes if needed.

## Files Added (Delete to Rollback)

### Backend - Domain
- `backend/domain/recommendation.py`
- `backend/domain/providers.py`

### Backend - Adapters
- `backend/adapters/mock_market_data.py`
- `backend/adapters/mock_fundamentals.py`
- `backend/adapters/mock_news.py`
- `backend/adapters/mock_sentiment.py`

### Backend - Services
- `backend/services/indicators.py`
- `backend/services/scoring.py`
- `backend/services/recommendation.py`

### Backend - Repository
- `backend/repo/recommendations.py`

### Backend - Routers
- `backend/routers/recommendations.py`

### Backend - Tests
- `backend/tests/test_indicators.py`
- `backend/tests/test_scoring.py`
- `backend/tests/test_recommendation_service.py`
- `backend/tests/test_recommendations_api.py`
- `backend/tests/fixtures/` (if created)

### Frontend - Pages
- `frontend/app/analyze/page.tsx`
- `frontend/app/results/[runId]/page.tsx`
- `frontend/app/history/page.tsx`

### Frontend - Components
- `frontend/components/ticker-input.tsx`
- `frontend/components/horizon-selector.tsx`
- `frontend/components/score-card.tsx`
- `frontend/components/allocation-chart.tsx`
- `frontend/components/evidence-panel.tsx`

### Frontend - Lib
- `frontend/lib/api.ts` (or revert if modified)

### Documentation
- `docs/features/F1-2-recommendation-engine/` (entire directory)

## Files Modified (Revert Changes)

### backend/main.py
Remove:
- Recommendations router import and include

### backend/routers/deps.py
Remove:
- Provider dependency injection
- RecommendationService dependency

### backend/pyproject.toml
Remove from dependencies (if added):
- `numpy`
- `pandas` (if used)

### frontend/app/dashboard/page.tsx
Remove:
- Link to /analyze
- Recent runs display

### frontend/package.json
Remove from dependencies (if added):
- Chart library for allocation visualization

### docs/feature.index.md
Change F1-2 status back to "Planned" and remove doc links

## Rollback Command

```bash
# Revert all F1-2 commits
git log --oneline | grep "F1-2" | awk '{print $1}' | xargs git revert --no-commit
git commit -m "Revert F1-2: Recommendation Engine"

# Or revert to specific commit before F1-2
git revert <first-F1-2-commit>..<last-F1-2-commit>
```

## Infrastructure Rollback

F1-2 does not introduce new AWS infrastructure. No CDK stacks to destroy.

Future phases that add infrastructure (DynamoDB for runs, external APIs) will require:
```bash
make infra-destroy ENV=dev FEATURE=F1-2
```

## Database/Storage Rollback

F1-2 uses in-memory storage only. No persistent data to clean up.

If upgraded to persistent storage in future:
- Delete DynamoDB table entries
- Or drop the entire table via CDK destroy

## Verification After Rollback

1. Backend starts without errors:
   ```bash
   cd backend && uvicorn main:app --reload
   ```

2. Health endpoint works:
   ```bash
   curl http://localhost:8000/health
   ```

3. Recommendation endpoints don't exist:
   ```bash
   curl http://localhost:8000/recommendations/analyze
   # Should return 404
   ```

4. Auth still works:
   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:8000/auth/me
   ```

5. Frontend builds:
   ```bash
   cd frontend && npm run build
   ```

6. All pre-F1-2 tests pass:
   ```bash
   cd backend && pytest tests/test_auth.py tests/test_health.py -v
   ```

7. No recommendation routes in frontend:
   - /analyze should 404
   - /results/[id] should 404
   - /history should 404

## Partial Rollback Options

### Backend Only
If frontend works but backend has issues:
1. Remove `backend/routers/recommendations.py`
2. Remove import from `backend/main.py`
3. Keep domain/services for future fix

### Frontend Only
If backend works but frontend has issues:
1. Delete `frontend/app/analyze/`
2. Delete `frontend/app/results/`
3. Delete `frontend/app/history/`
4. Remove dashboard links
5. API endpoints remain functional via curl/Postman
