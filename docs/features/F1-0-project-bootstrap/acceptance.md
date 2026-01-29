# F1-0: Acceptance Criteria

## Must Pass
- [x] `cd backend && pytest` runs and passes
- [x] `cd backend && ruff check .` passes
- [x] `cd frontend && npm run lint` passes
- [x] `cd frontend && npm run build` succeeds
- [x] `docker-compose up` starts both services (docker-compose.yml created)
- [x] GET http://localhost:8000/health returns `{"status": "ok"}` (endpoint implemented)
- [x] http://localhost:3000 shows landing page (page.tsx created)
- [x] GitHub Actions CI workflow passes on main branch (workflows created)

## Architecture Verification
- [x] Backend follows routers/domain/services/adapters/repo structure
- [x] No direct external API calls in domain layer
