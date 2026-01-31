# F1-2: Recommendation Engine (Basic Scoring) - Acceptance Criteria

## Prerequisites

- F1-1 (OAuth Authentication) must be complete and working
- User can log in and access protected routes
- Backend and frontend dev servers running

## Acceptance Criteria

### API - Analyze Endpoint

- [ ] `POST /recommendations/analyze` requires authentication
- [ ] Returns 401 without valid token
- [ ] Accepts valid ticker symbols (e.g., AAPL, MSFT, GOOGL)
- [ ] Rejects invalid ticker format
- [ ] Enforces max stocks per run (3 for free, 5 for pro)
- [ ] Returns 400 if too many tickers submitted
- [ ] Enforces horizon restrictions (free: 1M only)
- [ ] Returns 400 if free user selects non-1M horizon
- [ ] Returns complete `RecommendationResult` on success
- [ ] Result includes composite score for each stock
- [ ] Result includes score breakdown (technical, fundamental, sentiment)
- [ ] Result includes allocation weights
- [ ] Result includes evidence packet
- [ ] Returns unique `run_id` for each analysis

### API - Get Result Endpoint

- [ ] `GET /recommendations/{run_id}` requires authentication
- [ ] Returns 401 without valid token
- [ ] Returns 404 for non-existent run_id
- [ ] Returns 403 if run belongs to different user
- [ ] Returns complete result for valid run_id owned by user

### API - History Endpoint

- [ ] `GET /recommendations/history` requires authentication
- [ ] Returns 401 without valid token
- [ ] Returns empty list for new users
- [ ] Returns list of user's past runs
- [ ] Each item includes run_id, tickers, horizon, timestamp
- [ ] Does not include full evidence (summary only)

### Scoring Algorithm

- [ ] Technical indicators computed correctly (RSI, MACD, SMA)
- [ ] Technical score in range 0-100
- [ ] Fundamental score in range 0-100
- [ ] Sentiment score in range 0-100
- [ ] Composite score follows formula: 0.4*tech + 0.3*fund + 0.3*sent
- [ ] Stocks ranked by composite score (highest first)
- [ ] Allocation weights sum to 100%
- [ ] Higher scored stocks get higher allocation

### Frontend - Analyze Page (/analyze)

- [ ] Page requires authentication (redirects to /login if not)
- [ ] Displays ticker input field
- [ ] Displays horizon selector dropdown
- [ ] Shows plan-appropriate limits (3 tickers for free, 5 for pro)
- [ ] Horizon options restricted based on plan
- [ ] Free users see only "1 Month" option enabled
- [ ] Pro users see all horizon options
- [ ] Validates ticker input before submission
- [ ] Shows loading state during analysis
- [ ] Shows error message on failure
- [ ] Redirects to /results/[runId] on success

### Frontend - Results Page (/results/[runId])

- [ ] Page requires authentication
- [ ] Shows loading state while fetching
- [ ] Shows error if result not found
- [ ] Displays all scored stocks
- [ ] Each stock shows composite score prominently
- [ ] Each stock shows score breakdown (expandable)
- [ ] Shows allocation chart/visualization
- [ ] Shows evidence panel (collapsible)
- [ ] Shows horizon used for analysis
- [ ] Shows timestamp of analysis
- [ ] Educational disclaimer displayed

### Frontend - Dashboard Updates

- [ ] Dashboard shows link to "Run Analysis" (/analyze)
- [ ] Dashboard shows recent runs (if any)
- [ ] Click on run navigates to results page

### Code Quality

- [ ] All backend tests pass (`pytest`)
- [ ] Backend lint passes (`ruff check .`)
- [ ] Frontend builds without errors (`npm run build`)
- [ ] Frontend lint passes (`npm run lint`)
- [ ] No hardcoded secrets or API keys
- [ ] All providers use dependency injection

## Manual Testing Guide

### Test 1: Backend Unit Tests
```bash
cd backend
AUTH_MODE=mock pytest -v
```

### Test 2: Backend Lint
```bash
cd backend
ruff check .
```

### Test 3: Frontend Build
```bash
cd frontend
npm run build
```

### Test 4: Full Integration Test

1. Start backend: `cd backend && uvicorn main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Log in at http://localhost:3000/login
4. Navigate to /analyze
5. Enter tickers: AAPL, MSFT
6. Select horizon: 1 Month
7. Click "Analyze"
8. Verify redirect to /results/[runId]
9. Verify scores displayed for both stocks
10. Verify score breakdown visible
11. Verify allocation chart displayed
12. Navigate to /history
13. Verify the run appears in history

### Test 5: Plan Limit Enforcement (Free User)

1. Log in as free user
2. Navigate to /analyze
3. Try to enter 4+ tickers
4. Verify validation error or limit indicator
5. Verify only "1 Month" horizon is selectable

### Test 6: Plan Limit Enforcement (Pro User)

1. Log in as pro user (admin group = pro for testing)
2. Navigate to /analyze
3. Verify can enter up to 5 tickers
4. Verify all horizons are selectable
