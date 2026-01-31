# AlphaLens Makefile
# Standardized commands for infrastructure and development

.PHONY: help dev stop backend-dev frontend-dev \
        backend-install backend-test backend-lint backend-format \
        frontend-install frontend-build frontend-lint \
        test lint ci pr \
        infra-synth infra-diff infra-deploy infra-destroy hydrate-config

# Default target
help:
	@echo "╔═══════════════════════════════════════════════════════════════════╗"
	@echo "║                   AlphaLens Development Commands                  ║"
	@echo "╚═══════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "QUICK START"
	@echo "───────────────────────────────────────────────────────────────────"
	@echo "  make dev              Start backend + frontend (fresh)"
	@echo "  make stop             Stop all services"
	@echo ""
	@echo "DEVELOPMENT"
	@echo "───────────────────────────────────────────────────────────────────"
	@echo "  make backend-dev      Start backend only (port 8000)"
	@echo "  make frontend-dev     Start frontend only (port 3000)"
	@echo ""
	@echo "BACKEND"
	@echo "───────────────────────────────────────────────────────────────────"
	@echo "  make backend-install  Install Python dependencies"
	@echo "  make backend-test     Run pytest"
	@echo "  make backend-lint     Run ruff linter"
	@echo "  make backend-format   Format code with ruff"
	@echo ""
	@echo "FRONTEND"
	@echo "───────────────────────────────────────────────────────────────────"
	@echo "  make frontend-install Install npm dependencies"
	@echo "  make frontend-build   Build for production"
	@echo "  make frontend-lint    Run ESLint"
	@echo ""
	@echo "TESTING & CI"
	@echo "───────────────────────────────────────────────────────────────────"
	@echo "  make ci               Run full CI locally (lint + test + build)"
	@echo "  make test             Run all tests"
	@echo "  make lint             Run all linters"
	@echo ""
	@echo "PULL REQUESTS"
	@echo "───────────────────────────────────────────────────────────────────"
	@echo "  make pr FEATURE=F1-1  Create PR for feature"
	@echo ""
	@echo "INFRASTRUCTURE (CDK)"
	@echo "───────────────────────────────────────────────────────────────────"
	@echo "  make infra-synth   ENV=dev FEATURE=F1-1  Synthesize CloudFormation"
	@echo "  make infra-diff    ENV=dev FEATURE=F1-1  Show infrastructure diff"
	@echo "  make infra-deploy  ENV=dev FEATURE=F1-1  Deploy infrastructure"
	@echo "  make infra-destroy ENV=dev FEATURE=F1-1  Destroy infrastructure"
	@echo ""
	@echo "CONFIG"
	@echo "───────────────────────────────────────────────────────────────────"
	@echo "  make hydrate-config ENV=dev  Fetch config from SSM"
	@echo ""
	@echo "LOGS (after make dev)"
	@echo "───────────────────────────────────────────────────────────────────"
	@echo "  tail -f /tmp/alphalens-backend.log"
	@echo "  tail -f /tmp/alphalens-frontend.log"
	@echo ""

# Environment validation
ENV ?= dev
FEATURE ?=

# Infrastructure commands
infra-synth:
	@echo "Synthesizing infrastructure for ENV=$(ENV) FEATURE=$(FEATURE)"
	cd infra && INFRA_ENV=$(ENV) INFRA_FEATURE=$(FEATURE) npx cdk synth $(if $(FEATURE),-c feature=$(FEATURE),)

infra-diff:
	@echo "Showing infrastructure diff for ENV=$(ENV) FEATURE=$(FEATURE)"
	cd infra && INFRA_ENV=$(ENV) INFRA_FEATURE=$(FEATURE) npx cdk diff $(if $(FEATURE),-c feature=$(FEATURE),)

infra-deploy:
	@echo "Deploying infrastructure for ENV=$(ENV) FEATURE=$(FEATURE)"
	cd infra && INFRA_ENV=$(ENV) INFRA_FEATURE=$(FEATURE) npx cdk deploy --require-approval never $(if $(FEATURE),-c feature=$(FEATURE),)

infra-destroy:
	@echo "Destroying infrastructure for ENV=$(ENV) FEATURE=$(FEATURE)"
	cd infra && INFRA_ENV=$(ENV) INFRA_FEATURE=$(FEATURE) npx cdk destroy --force $(if $(FEATURE),-c feature=$(FEATURE),)

# Config hydration from SSM
hydrate-config:
	@echo "Hydrating config from SSM for ENV=$(ENV)"
	@./scripts/hydrate-config.sh $(ENV)

# Stop all running services (thorough cleanup for WSL)
stop:
	@echo "Stopping AlphaLens services..."
	@-pkill -f "uvicorn main:app" 2>/dev/null || true
	@-pkill -f "next dev" 2>/dev/null || true
	@-pkill -f "next-server" 2>/dev/null || true
	@sleep 1
	@-lsof -ti:8000 | xargs -r kill -9 2>/dev/null || true
	@-lsof -ti:3000,3001,3002,3003 | xargs -r kill -9 2>/dev/null || true
	@sleep 1
	@echo "All services stopped"

# Development servers
backend-dev:
	cd backend && AUTH_MODE=mock uvicorn main:app --reload

frontend-dev:
	cd frontend && npm run dev

# Start everything fresh (stops existing, then starts both)
dev: stop
	@sleep 1
	@echo "Starting backend (AUTH_MODE=mock)..."
	@cd backend && AUTH_MODE=mock nohup uvicorn main:app --reload > /tmp/alphalens-backend.log 2>&1 &
	@sleep 3
	@echo "Starting frontend..."
	@cd frontend && nohup npm run dev > /tmp/alphalens-frontend.log 2>&1 &
	@sleep 5
	@echo ""
	@echo "========================================="
	@echo "AlphaLens is running!"
	@echo "========================================="
	@echo "Frontend: http://localhost:3000/login"
	@echo "Backend:  http://localhost:8000"
	@echo ""
	@echo "Logs:"
	@echo "  Backend:  tail -f /tmp/alphalens-backend.log"
	@echo "  Frontend: tail -f /tmp/alphalens-frontend.log"
	@echo ""
	@echo "Stop with: make stop"
	@echo "========================================="

# Testing
test:
	cd backend && pytest -v
	cd frontend && npm run lint

# Linting
lint:
	cd backend && ruff check .
	cd frontend && npm run lint

# Backend specific
backend-install:
	cd backend && pip install -e .[dev]

backend-test:
	cd backend && pytest -v

backend-lint:
	cd backend && ruff check .

backend-format:
	cd backend && ruff format .

# Frontend specific
frontend-install:
	cd frontend && npm install

frontend-build:
	cd frontend && npm run build

frontend-lint:
	cd frontend && npm run lint

# ============================================
# CI & Pull Request Commands
# ============================================

# Run full CI locally (same as GitHub Actions)
ci:
	@echo "========================================="
	@echo "Running CI locally..."
	@echo "========================================="
	@echo ""
	@echo "[1/4] Backend lint..."
	@cd backend && ruff check .
	@echo ""
	@echo "[2/4] Backend tests..."
	@cd backend && AUTH_MODE=mock pytest -v
	@echo ""
	@echo "[3/4] Frontend lint..."
	@cd frontend && npm run lint
	@echo ""
	@echo "[4/4] Frontend build..."
	@cd frontend && npm run build
	@echo ""
	@echo "========================================="
	@echo "CI PASSED - Ready to create PR"
	@echo "========================================="

# Create PR for feature
pr:
ifndef FEATURE
	$(error FEATURE is required. Usage: make pr FEATURE=F1-1)
endif
	@echo "Creating PR for $(FEATURE)..."
	@git push -u origin HEAD
	@gh pr create --fill --title "$(FEATURE): $(shell git log -1 --pretty=%s)"
	@echo ""
	@echo "PR created! CI will run automatically."
