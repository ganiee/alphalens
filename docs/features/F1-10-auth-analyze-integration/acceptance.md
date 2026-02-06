# F1-10: Acceptance Criteria

## Core Requirements

### AC1: Authenticated Access Required
- [ ] Unauthenticated request to `/recommendations/analyze` returns 401
- [ ] Unauthenticated request to `/recommendations/{run_id}` returns 401
- [ ] Unauthenticated request to `/recommendations/` returns 401

### AC2: Token Verification
- [ ] Valid JWT token allows access to protected endpoints
- [ ] Invalid JWT token returns 401
- [ ] Expired JWT token returns 401
- [ ] Malformed Authorization header returns 401

### AC3: User Attribution
- [ ] Run results contain `user_id` from token's `sub` claim
- [ ] User can only access their own results (403 otherwise)
- [ ] History endpoint filters by authenticated user's ID

### AC4: Frontend Integration
- [ ] Analyze page requires login (redirects if not authenticated)
- [ ] Results page requires login
- [ ] History page requires login
- [ ] API calls include Authorization header with Bearer token

### AC5: Repository Interface
- [ ] RunRepository Protocol is defined
- [ ] InMemoryRunRepository implements the Protocol
- [ ] Interface supports future database implementations

## Verification Steps

### Manual Testing

1. **Without Authentication:**
   ```bash
   curl -X POST http://localhost:8000/recommendations/analyze \
     -H "Content-Type: application/json" \
     -d '{"tickers": ["AAPL"], "horizon": "1M"}'
   # Expected: 401 Unauthorized
   ```

2. **With Invalid Token:**
   ```bash
   curl -X POST http://localhost:8000/recommendations/analyze \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer invalid-token" \
     -d '{"tickers": ["AAPL"], "horizon": "1M"}'
   # Expected: 401 Unauthorized
   ```

3. **With Valid Token (Mock Mode):**
   ```bash
   curl -X POST http://localhost:8000/recommendations/analyze \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer test-user-token" \
     -d '{"tickers": ["AAPL"], "horizon": "1M"}'
   # Expected: 200 OK with result containing user_id
   ```

4. **Frontend Flow:**
   - Start app in mock mode
   - Navigate to /analyze without logging in
   - Verify redirect to /login
   - Log in with mock credentials
   - Navigate to /analyze
   - Submit analysis
   - Verify result page shows data
   - Verify history page shows the run

### Automated Testing

```bash
cd backend
AUTH_MODE=mock pytest -v tests/test_auth.py tests/test_recommendations_api.py
```

All tests must pass.

## Sign-off

- [ ] All automated tests pass
- [ ] Manual testing completed
- [ ] Code review approved
- [ ] Documentation complete
