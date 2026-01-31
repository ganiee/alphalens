# AlphaLens Makefile
# Standardized commands for infrastructure and development

.PHONY: help infra-synth infra-diff infra-deploy infra-destroy backend-dev frontend-dev test lint ci pr

# Default target
help:
	@echo "AlphaLens Development Commands"
	@echo ""
	@echo "Development:"
	@echo "  make dev           - Start backend + frontend (fresh)"
	@echo "  make stop          - Stop all services"
	@echo "  make backend-dev   - Start backend only"
	@echo "  make frontend-dev  - Start frontend only"
	@echo ""
	@echo "Testing & CI:"
	@echo "  make ci            - Run full CI locally (lint + test + build)"
	@echo "  make test          - Run all tests"
	@echo "  make lint          - Run linters"
	@echo ""
	@echo "Pull Requests:"
	@echo "  make pr FEATURE=<FeatureID>  - Create PR for feature"
	@echo ""
	@echo "Infrastructure (CDK):"
	@echo "  make infra-deploy ENV=<env> FEATURE=<FeatureID>  - Deploy infrastructure"
	@echo "  make infra-destroy ENV=<env> FEATURE=<FeatureID> - Destroy infrastructure"
	@echo ""
	@echo "Config:"
	@echo "  make hydrate-config ENV=<env>  - Fetch config from SSM"

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

# Stop all running services
stop:
	@pkill -f "uvicorn" 2>/dev/null || true
	@pkill -f "next" 2>/dev/null || true
	@sleep 1
	@echo "All services stopped"

# Development servers
backend-dev:
	cd backend && uvicorn main:app --reload

frontend-dev:
	cd frontend && npm run dev

# Start everything fresh (stops existing, then starts both)
dev:
	@echo "Stopping existing services..."
	@pkill -f "uvicorn" 2>/dev/null || true
	@pkill -f "next" 2>/dev/null || true
	@sleep 2
	@echo "Starting backend..."
	@cd backend && nohup uvicorn main:app --reload > /tmp/alphalens-backend.log 2>&1 &
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
