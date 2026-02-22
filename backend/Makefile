# Makefile for AI Chat Backend

.PHONY: help build up down logs clean dev prod migrate shell

# Default target
help: ## Show this help message
	@echo "AI Chat Backend - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development commands
dev: ## Start development environment
	docker-compose up --build

dev-bg: ## Start development environment in background
	docker-compose up -d --build

dev-logs: ## View development logs
	docker-compose logs -f

dev-down: ## Stop development environment
	docker-compose down

# Production commands
prod: ## Start production environment
	docker-compose -f docker-compose.prod.yml up -d --build

prod-logs: ## View production logs
	docker-compose -f docker-compose.prod.yml logs -f

prod-down: ## Stop production environment
	docker-compose -f docker-compose.prod.yml down

# Database commands
migrate: ## Run database migrations
	docker-compose exec app alembic upgrade head

migrate-create: ## Create new migration (usage: make migrate-create MESSAGE="description")
	docker-compose exec app alembic revision --autogenerate -m "$(MESSAGE)"

db-shell: ## Access database shell
	docker-compose exec db psql -U postgres -d ai_chat_db

# Utility commands
build: ## Build Docker images
	docker-compose build

clean: ## Clean up Docker resources
	docker-compose down -v
	docker system prune -f

shell: ## Access application container shell
	docker-compose exec app /bin/bash

# Health check
health: ## Check application health
	curl -f http://localhost:8000/health || echo "Application is not running"

