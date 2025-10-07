# CSR Lambda API System - Development Commands

.PHONY: help setup-dev setup-staging setup-prod start stop clean test lint

# Default environment
ENV ?= dev

help: ## Show this help message
	@echo "CSR Lambda API System - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup-dev: ## Setup development environment
	@echo "Setting up development environment..."
	@./scripts/setup-env.sh dev
	@echo "Development environment ready!"

setup-staging: ## Setup staging environment
	@echo "Setting up staging environment..."
	@./scripts/setup-env.sh staging
	@echo "Staging environment ready!"

setup-prod: ## Setup production environment
	@echo "Setting up production environment..."
	@./scripts/setup-env.sh prod
	@echo "Production environment ready!"

start: ## Start all services with Docker Compose
	@echo "Starting all services..."
	@docker-compose up -d
	@echo "Services started! Frontend: http://localhost:3000, Backend: http://localhost:8000"

stop: ## Stop all services
	@echo "Stopping all services..."
	@docker-compose down

clean: ## Clean up Docker containers and volumes
	@echo "Cleaning up..."
	@docker-compose down -v
	@docker system prune -f

test: ## Run all tests
	@echo "Running backend tests..."
	@cd backend && python -m pytest
	@echo "Running frontend tests..."
	@cd frontend && npm test

lint: ## Run linting for all code
	@echo "Linting backend code..."
	@cd backend && python -m flake8 app/
	@echo "Linting frontend code..."
	@cd frontend && npm run lint

install-backend: ## Install backend dependencies
	@echo "Installing backend dependencies..."
	@cd backend && pip install -r requirements.txt

install-frontend: ## Install frontend dependencies
	@echo "Installing frontend dependencies..."
	@cd frontend && npm install

dev-backend: ## Run backend in development mode
	@echo "Starting backend development server..."
	@cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Run frontend in development mode
	@echo "Starting frontend development server..."
	@cd frontend && npm run dev

logs: ## Show Docker Compose logs
	@docker-compose logs -f

status: ## Show status of all services
	@docker-compose ps

# Development Environment Management
dev-start: ## Start development environment with health checks
	@echo "Starting development environment..."
	@./scripts/dev-setup.sh start

dev-stop: ## Stop development environment
	@echo "Stopping development environment..."
	@./scripts/dev-setup.sh stop

dev-restart: ## Restart development environment
	@echo "Restarting development environment..."
	@./scripts/dev-setup.sh restart

dev-status: ## Show detailed development environment status
	@./scripts/dev-setup.sh status

dev-logs: ## Show logs for all services (use dev-logs-backend, dev-logs-frontend, dev-logs-mysql for specific services)
	@./scripts/dev-setup.sh logs

dev-logs-backend: ## Show backend logs
	@./scripts/dev-setup.sh logs backend

dev-logs-frontend: ## Show frontend logs
	@./scripts/dev-setup.sh logs frontend

dev-logs-mysql: ## Show MySQL logs
	@./scripts/dev-setup.sh logs mysql

dev-cleanup: ## Clean up all development containers and volumes
	@./scripts/dev-setup.sh cleanup

dev-shell-backend: ## Open shell in backend container
	@docker exec -it csr-lambda-backend /bin/bash

dev-shell-mysql: ## Open MySQL shell
	@docker exec -it csr-lambda-mysql mysql -u dev_user -p csr_lambda_dev

# AWS Cognito Setup
setup-cognito: ## Setup AWS Cognito User Pool and App Client for development
	@./scripts/setup-cognito.sh

# AWS Aurora MySQL Setup
setup-aurora: ## Setup AWS Aurora MySQL cluster for development
	@./scripts/setup-dev-aurora.sh

sync-to-aurora: ## Sync local MySQL data to Aurora MySQL
	@./scripts/sync-local-to-aurora.sh

# Database Management
use-local-db: ## Switch backend to use local MySQL
	@cp backend/.env.dev backend/.env.dev.current
	@echo "✅ Switched to local MySQL database"
	@echo "Restart development environment: make dev-restart"

use-aurora-db: ## Switch backend to use Aurora MySQL
	@if [ -f backend/.env.dev.aurora ]; then \
		cp backend/.env.dev.aurora backend/.env.dev; \
		echo "✅ Switched to Aurora MySQL database"; \
		echo "Restart development environment: make dev-restart"; \
	else \
		echo "❌ Aurora environment file not found. Run: make setup-aurora"; \
	fi