.PHONY: help install format test lint type-check security benchmark clean docker-build docker-run

help: ## Show this help message
	@echo "Wordle Bot - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync --all-extras

format: ## Format code with black and isort
	./format.sh

test: ## Run tests
	PYTHONPATH=libs uv run pytest libs/*/tests/ -v

lint: ## Run linting
	PYTHONPATH=libs uv run flake8 libs/ apps/ --max-line-length=88 --max-complexity=10

type-check: ## Run type checking
	PYTHONPATH=libs uv run basedpyright .

security: ## Run security checks
	PYTHONPATH=libs uv run safety check
	PYTHONPATH=libs uv run bandit -r libs/ apps/

benchmark: ## Run performance benchmark
	PYTHONPATH=libs uv run python -m apps.cli.main benchmark --quick

cli: ## Run CLI app
	PYTHONPATH=libs uv run python -m apps.cli.main

api: ## Run API app
	PYTHONPATH=libs uv run uvicorn apps.api.app:app --host 0.0.0.0 --port 8000 --reload

docker-build: ## Build Docker images
	docker build -f Dockerfile.cli -t wordle-bot-cli:latest .
	docker build -f Dockerfile.api -t wordle-bot-api:latest .

docker-run: ## Run with Docker Compose
	docker-compose -f docker-compose.dev.yml up --build

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf dist/ build/

ci: format lint type-check test ## Run all CI checks

all: install ci security benchmark ## Run everything
