# F1-0: Project Bootstrap & CI/CD

## Overview
Initialize the AlphaLens project structure with frontend (Next.js) and backend (FastAPI) scaffolding, establish the CI/CD pipeline, and configure development tooling.

## Scope

### Frontend (Next.js)
- Next.js 14+ with TypeScript
- App Router structure
- Tailwind CSS for styling
- ESLint + Prettier configuration
- Mobile-first responsive setup

### Backend (FastAPI)
- Python 3.12+ with FastAPI
- Ports & Adapters architecture:
  ```
  backend/
  ├── routers/        # HTTP endpoints
  ├── domain/         # Business entities
  ├── services/       # Use cases
  ├── adapters/       # External integrations (stubs)
  └── repo/           # Data persistence (stubs)
  ```
- pytest configuration
- Ruff for linting/formatting

### CI/CD
- GitHub Actions workflow:
  - Lint (frontend + backend)
  - Type check
  - Test (unit tests)
- Branch protection rules documentation

### DevOps
- Docker Compose for local development
- Environment variable templates (.env.example)

## Out of Scope
- Actual deployment to Vercel/AWS (infrastructure setup is Phase 1 but separate)
- Authentication implementation (F1-1)
- Database setup beyond stubs

## Dependencies
None (first feature)
