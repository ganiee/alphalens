# F1-1: OAuth Authentication & Roles - Rollback Plan

## Overview

This document describes how to rollback F1-1 authentication changes if needed.

## Files Added (Delete to Rollback)

### Backend
- `backend/domain/auth.py`
- `backend/domain/settings.py`
- `backend/adapters/cognito_auth.py`
- `backend/adapters/mock_auth.py`
- `backend/routers/deps.py`
- `backend/routers/auth.py`
- `backend/tests/test_auth.py`

### Frontend
- `frontend/lib/amplify-config.ts`
- `frontend/lib/auth-context.tsx`
- `frontend/app/providers.tsx`
- `frontend/app/login/page.tsx`
- `frontend/app/register/page.tsx`
- `frontend/app/signout/page.tsx`
- `frontend/app/dashboard/page.tsx`
- `frontend/components/protected-route.tsx`

### Config
- `config/auth.yaml`

### Documentation
- `docs/features/F1-1-oauth-auth/` (entire directory)

## Files Modified (Revert Changes)

### backend/main.py
Remove:
- CORS middleware configuration
- Auth router import and include
- Settings import

### backend/pyproject.toml
Remove from dependencies:
- `python-jose[cryptography]>=3.3.0`
- `httpx>=0.26.0`

### backend/.env.example
Revert to remove:
- AUTH_MODE
- COGNITO_* variables
- CORS_ORIGINS

### frontend/package.json
Remove from dependencies:
- `aws-amplify`
- `@aws-amplify/adapter-nextjs`

### frontend/app/layout.tsx
Remove Providers wrapper, restore original:
```tsx
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50">{children}</body>
    </html>
  );
}
```

### frontend/.env.example
Remove COGNITO_* and AWS_REGION variables

### docs/prd.base.md
Revert line 36-37 to include Facebook OAuth

### docs/feature.index.md
Change F1-1 status back to "Planned" and remove doc links

## Rollback Command

```bash
git revert <commit-hash>
```

## Infrastructure Rollback

### CDK Destroy Command
```bash
make infra-destroy ENV=dev FEATURE=F1-1
```

This will delete:
- Cognito User Pool
- Cognito App Client
- Cognito Hosted UI Domain
- SSM Parameters (`/alphalens/dev/auth/*`)

### Manual AWS Console Rollback (if CDK fails)
1. Go to Cognito > User Pools
2. Select the alphalens user pool
3. Delete (this is safe if no production users exist)
4. Go to Systems Manager > Parameter Store
5. Delete parameters under `/alphalens/dev/auth/`

### Infrastructure Files to Remove
- `/infra/features/F1-1-oauth-auth/` (entire directory)
- Update `/docs/infra/infra-index.md` to remove F1-1 entry

## Verification After Rollback

1. Backend starts without errors: `uvicorn main:app --reload`
2. Health endpoint works: `curl http://localhost:8000/health`
3. No auth endpoints exist: `curl http://localhost:8000/auth/me` returns 404
4. Frontend builds: `npm run build`
5. All original tests pass
6. CDK stack no longer exists: `aws cloudformation describe-stacks --stack-name alphalens-dev-F1-1-cognito` returns error
