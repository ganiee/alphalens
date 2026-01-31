# F1-1: OAuth Authentication & Roles - Acceptance Criteria

## Prerequisites

Before testing, complete the AWS setup:

1. Create Cognito User Pool in AWS Console
2. Create App Client (public client type)
3. Configure Hosted UI domain
4. (Optional) Add Google identity provider
5. Fill in `config/auth.yaml` with your values
6. Create `.env` files from `.env.example` templates

## Acceptance Criteria

### Login Page (Plan Selection)

- [x] `/login` displays two plan cards: Free and Pro
- [x] Plan cards show features for each plan
- [x] "Continue" button is disabled until a plan is selected
- [x] Selecting a plan enables the "Continue" button
- [x] Clicking "Continue" redirects to Cognito Hosted UI
- [x] Clear disclaimer about educational purposes

### Backend Authentication

- [x] `GET /auth/me` returns 401 without token
- [x] `GET /auth/me` returns 401 with invalid token
- [x] `GET /auth/me` returns user info with valid token
- [x] `GET /auth/admin/check` returns 403 for non-admin users
- [x] `GET /auth/admin/check` returns 200 for admin users
- [x] `GET /health` remains publicly accessible

### Frontend Authentication (Hosted UI Flow)

- [ ] Users can sign up via Cognito Hosted UI
- [ ] Users receive email verification after registration
- [ ] Users can sign in via Hosted UI (email/password)
- [ ] Users can sign in via Google OAuth (if configured)
- [ ] After auth, users redirected back to app
- [ ] Users can sign out
- [ ] Unauthenticated users redirected to /login on protected routes

### Dashboard

- [x] Shows user email
- [x] Shows selected plan (Free or Pro)
- [x] Shows user roles
- [x] Shows email verification status
- [x] Sign Out button works (redirects to /signout)
- [x] Disclaimer displayed

### Sign Out (/signout)

- [x] Clears localStorage
- [x] Clears sessionStorage
- [x] Signs out from Cognito globally
- [x] Redirects to /login after completion
- [x] Direct access to /signout clears stale sessions

### Security

- [x] JWT tokens validated against Cognito JWKS
- [x] Expired tokens rejected
- [x] CORS configured for allowed origins
- [x] No secrets in frontend code

### Code Quality

- [x] All backend auth tests pass
- [x] Backend passes ruff lint
- [x] Frontend builds without errors
- [x] Frontend passes eslint

## Manual Testing Guide

### Test 1: Backend Unit Tests
```bash
cd backend
pytest tests/test_auth.py -v
```

### Test 2: Backend Lint
```bash
cd backend
ruff check .
```

### Test 3: Frontend Build
```bash
cd frontend
npm install
npm run build
```

### Test 4: Full Integration (requires AWS setup)

1. Start backend: `cd backend && uvicorn main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Navigate to http://localhost:3000/login
4. Verify plan cards are displayed (Free and Pro)
5. Verify "Continue" button is disabled
6. Select a plan (e.g., Free)
7. Verify "Continue" button is enabled
8. Click "Continue" → should redirect to Cognito Hosted UI
9. Sign in or create account via Hosted UI
10. After auth, verify redirect back to /dashboard
11. Verify dashboard shows correct email and plan
12. Test Sign Out
