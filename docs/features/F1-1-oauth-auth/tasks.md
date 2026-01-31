# F1-1: OAuth Authentication & Roles - Tasks

## Completed Tasks

### Phase A: Backend Foundation
- [x] Create `domain/auth.py` with User, TokenPayload, UserRole, UserPlan entities
- [x] Create `domain/settings.py` with Cognito configuration
- [x] Create `adapters/mock_auth.py` for testing
- [x] Create `routers/deps.py` with FastAPI dependencies
- [x] Create `routers/auth.py` with /me and /admin/check endpoints
- [x] Write `tests/test_auth.py` with comprehensive test coverage

### Phase B: Cognito Integration
- [x] Add python-jose and httpx to pyproject.toml
- [x] Create `adapters/cognito_auth.py` with JWKS caching
- [x] Update backend/.env.example with Cognito variables
- [x] Update main.py to include auth router and CORS

### Phase C: Frontend Foundation (Hosted UI)
- [x] Add AWS Amplify dependencies to package.json
- [x] Create `lib/amplify-config.ts` for Cognito Hosted UI configuration
- [x] Create `lib/auth-context.tsx` with Hub listener for Hosted UI callbacks
- [x] Create `app/providers.tsx` to initialize Amplify
- [x] Update `app/layout.tsx` to wrap with providers

### Phase D: Frontend Pages (Plan Selection + Hosted UI)
- [x] Create `app/login/page.tsx` with plan cards (Free/Pro) and Hosted UI redirect
- [x] Update `app/register/page.tsx` to redirect to /login (Hosted UI handles registration)
- [x] Create `app/dashboard/page.tsx` as protected route with plan display
- [x] Create `app/signout/page.tsx` to clear all auth state and redirect to login
- [x] Create `components/protected-route.tsx` HOC

### Phase E: Configuration & Documentation
- [x] Create `config/auth.yaml` template
- [x] Update frontend/.env.example
- [x] Update docs/prd.base.md (remove Facebook OAuth)
- [x] Create feature documentation in docs/features/F1-1-oauth-auth/

## Pending Tasks

- [ ] AWS Cognito User Pool setup (manual, see acceptance.md)
- [ ] Google OAuth provider configuration in Cognito (optional)
- [ ] Production deployment configuration
- [ ] Persist plan selection to backend (future: link to Stripe)
