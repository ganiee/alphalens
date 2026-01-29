# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AlphaLens is an AI-powered stock analysis and recommendation platform. It uses deterministic scoring combined with LLM-generated explanations (LLMs summarize, never decide).

## Tech Stack

- **Frontend**: Next.js 14 (TypeScript, React, Tailwind), hosted on Vercel
- **Backend**: Python 3.12+ FastAPI, hosted on AWS ECS Fargate
- **Auth**: Amazon Cognito with OAuth (Google, Facebook)

## Commands

### Backend
```bash
cd backend
pip install -e .[dev]      # Install with dev dependencies
pytest                      # Run tests
pytest -v tests/test_health.py::test_health_check_returns_ok  # Single test
ruff check .               # Lint
ruff format .              # Format
uvicorn main:app --reload  # Run dev server (port 8000)
```

### Frontend
```bash
cd frontend
npm install                # Install dependencies
npm run dev                # Run dev server (port 3000)
npm run build              # Production build
npm run lint               # Lint
```

### Docker
```bash
docker-compose up          # Run both services
docker-compose up backend  # Run backend only
```

## Backend Architecture

Ports & Adapters (Clean Architecture) with this layering:
```
routers/      # HTTP endpoints
domain/       # Business logic, entities
services/     # Use cases, orchestration
adapters/     # External service implementations
repo/         # Data persistence
```

Required interfaces (ports):
- MarketDataProvider, FundamentalsProvider, NewsProvider
- SentimentAnalyzer, LLMClient, RecommendationEngine
- CostMeter, AuthVerifier

Recommendation pipeline: `FetchData → ComputeFeatures → Score → Rank → Allocate → Explain`

## Development Governance

### Index Files (Source of Truth)
- `docs/phase.index.md` - Phase states (Planned/Active/Frozen)
- `docs/feature.index.md` - Feature tracking

### Feature IDs
Format: `F<phase>-<number>` (e.g., F1-1, F1.5-2, F2-3)
- IDs are immutable once assigned
- One feature In Progress at a time

### Feature Documentation
Each feature requires:
```
docs/features/F<phase>-<n>-short-name/
├── spec.md
├── tasks.md
├── tests.md
├── acceptance.md
└── rollback.md
```

### Completion Requirements
A feature may only be marked Complete when:
- Feature-scoped tests exist and pass
- Acceptance criteria verified
- Feature index status updated

## Testing Policy

- External boundaries must be mocked (market data, LLM, auth, etc.)
- Domain logic tested without network calls
- Use fixed, versioned fixtures
- No flaky tests (no live endpoints or current time dependencies)

## Product Principles

- Explainability over black-box predictions
- Cost-aware by design (usage limits, caching, metering)
- Mobile-first responsive design
- Educational purposes only disclaimers required