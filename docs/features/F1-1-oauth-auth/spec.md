# F1-1: OAuth Authentication & Roles - Specification

## Overview

This feature implements user authentication using Amazon Cognito with:
- Cognito Hosted UI for sign-in/sign-up (redirect-based flow)
- Google OAuth social login (via Hosted UI)
- Email/password registration (via Hosted UI)
- Plan selection (Free/Pro) before authentication
- Role-based access control (user/admin)
- Protected routes on both frontend and backend

## Architecture

### Backend (FastAPI)

**Ports & Adapters Pattern:**
- **Port**: `AuthVerifier` protocol in `domain/auth.py`
- **Adapters**:
  - `MockAuthVerifier` - For testing without AWS
  - `CognitoAuthVerifier` - Production JWT verification

**Domain Entities:**
- `User` - Authenticated user with roles and plan
- `TokenPayload` - JWT claims extracted from Cognito token
- `UserRole` - Enum: user, admin
- `UserPlan` - Enum: free, pro

**Endpoints:**
- `GET /auth/me` - Returns current user info (requires auth)
- `GET /auth/admin/check` - Admin-only endpoint

### Frontend (Next.js + Amplify)

**Auth Flow (Hosted UI):**
1. User visits `/login`
2. User selects plan (Free or Pro) - required before continuing
3. User clicks "Continue" → redirects to Cognito Hosted UI
4. User signs in/up via Hosted UI (email or Google)
5. Cognito redirects back to app with auth code
6. Amplify exchanges code for tokens
7. User redirected to `/dashboard`

**Components:**
- `AuthProvider` - React context for auth state with Hub listener
- `ProtectedRoute` - HOC for authenticated routes

**Pages:**
- `/login` - Plan selection cards + Continue button → Hosted UI
- `/register` - Redirects to `/login` (Hosted UI handles registration)
- `/dashboard` - Protected user dashboard showing plan info
- `/signout` - Clears all auth state (localStorage, sessionStorage, Cognito) and redirects to login

## UI Contract

Following Base UI Contract (prd.base):
- Mobile-first responsive design
- Calm, professional UI (no trading/gambling visuals)
- Progressive disclosure for advanced details
- Clear disclaimers (educational only)

## Security

- JWT tokens verified using Cognito JWKS
- JWKS cached for 1 hour to reduce latency
- Bearer token required in Authorization header
- CORS configured for allowed origins
- No secrets in client-side code
- Selected plan stored in sessionStorage (client-side only for now)

## Configuration

Environment variables:
- `AUTH_MODE` - "mock" or "cognito"
- `AWS_REGION` - AWS region
- `COGNITO_USER_POOL_ID` - Cognito pool ID
- `COGNITO_CLIENT_ID` - App client ID
- `COGNITO_DOMAIN` - Hosted UI domain

## Dependencies

### Backend
- `python-jose[cryptography]` - JWT verification
- `httpx` - HTTP client for JWKS fetching

### Frontend
- `aws-amplify` - Cognito SDK with Hosted UI support
- `@aws-amplify/adapter-nextjs` - Next.js SSR support

## Infrastructure

### Stack Information
- **Stack Name**: `alphalens-<env>-F1-1-cognito`
- **Module Path**: `/infra/features/F1-1-oauth-auth/`
- **CDK File**: `stack.ts`

### Resources Provisioned
- Cognito User Pool
- Cognito App Client (public, PKCE)
- Cognito Hosted UI Domain
- User Groups: `admin`, `pro`
- SSM Parameters for config hydration

### SSM Parameters
- `/alphalens/<env>/auth/userPoolId`
- `/alphalens/<env>/auth/clientId`
- `/alphalens/<env>/auth/domain`
- `/alphalens/<env>/auth/region`

### Deploy Commands
```bash
make infra-deploy ENV=dev FEATURE=F1-1
make infra-destroy ENV=dev FEATURE=F1-1
```

### Config Hydration
```bash
make hydrate-config ENV=dev
```
