# F1-10: Tasks

## Backend Tasks

### B1. Create RunRepository Protocol
- [ ] Create `backend/domain/run_repository.py` with Protocol definition
- [ ] Define methods: save, get_by_id, get_by_user, delete
- [ ] Add type hints for future database implementations

### B2. Refactor RecommendationRepository
- [ ] Move implementation to `backend/repo/in_memory.py`
- [ ] Implement RunRepository Protocol
- [ ] Update imports in `deps.py`

### B3. Verify Auth Middleware (Already Done)
- [x] Token verification in `get_token_payload`
- [x] User extraction in `get_current_user`
- [x] 401 response for missing/invalid tokens

### B4. Verify Protected Endpoints (Already Done)
- [x] `/recommendations/analyze` requires auth
- [x] `/recommendations/{run_id}` requires auth + ownership
- [x] `/recommendations/` requires auth + filters by user

## Frontend Tasks

### F1. Verify Auth Header Integration (Already Done)
- [x] API client includes Bearer token
- [x] Token passed from auth context

### F2. Verify Protected Routes (Already Done)
- [x] `/analyze` wrapped in ProtectedRoute
- [x] `/results/[runId]` wrapped in ProtectedRoute
- [x] `/history` wrapped in ProtectedRoute

### F3. Add 401 Handling (Already Done)
- [x] ApiError class handles 401 responses
- [x] ProtectedRoute redirects to login

## Testing Tasks

### T1. Verify Existing Tests (Already Done)
- [x] `test_analyze_requires_auth`
- [x] `test_get_result_requires_auth`
- [x] `test_get_result_wrong_user`
- [x] `test_history_requires_auth`
- [x] `test_history_excludes_other_users`

### T2. Add Repository Interface Tests
- [ ] Test InMemoryRunRepository implements Protocol
- [ ] Test type compatibility with Protocol

## Documentation Tasks

### D1. Create Feature Documentation
- [x] spec.md
- [x] tasks.md
- [ ] tests.md
- [ ] acceptance.md
- [ ] rollback.md

### D2. Update OpenAPI Spec
- [ ] Verify all auth requirements documented
- [ ] Verify error responses documented
