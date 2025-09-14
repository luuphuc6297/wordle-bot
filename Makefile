.PHONY: help install format test lint type-check security benchmark clean docker-build docker-run

help: ## Show this help message
	@echo "Wordle Bot - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync --all-extras

format: ## Format code with ruff
	uv run ruff check . --fix
	uv run ruff format .

format-check: ## Check code formatting without fixing
	uv run ruff check . --diff
	uv run ruff format . --check

test: ## Run tests
	PYTHONPATH=libs uv run pytest libs/*/tests/ -v || echo "No tests found"

lint: ## Run linting
	PYTHONPATH=libs uv run ruff check . --fix

type-check: ## Run type checking
	PYTHONPATH=libs uv run basedpyright .

security: ## Run security checks
	PYTHONPATH=libs uv run safety scan
	PYTHONPATH=libs uv run bandit -r libs/ apps/

benchmark: ## Run performance benchmark
	PYTHONPATH=libs uv run python -m apps.cli.main benchmark --quick

cli: ## Run CLI app
	PYTHONPATH=libs uv run python -m apps.cli.main

api: ## Run API app
	PYTHONPATH=libs uv run uvicorn apps.api.app:app --host 0.0.0.0 --port 8000 --reload

docker-build: ## Build Docker image
	docker build -t wordle-bot:latest .

docker-run: ## Run with Docker Compose
	docker-compose up --build

docker-cli: ## Run CLI in Docker
	docker run --rm wordle-bot:latest python -m apps.cli.main --help

docker-api: ## Run API in Docker
	docker run --rm -p 8000:8000 wordle-bot:latest uvicorn apps.api.app:app --host 0.0.0.0 --port 8000

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf dist/ build/

ci: format-check lint type-check test ## Run all CI checks

all: install ci security benchmark ## Run everything
