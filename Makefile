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