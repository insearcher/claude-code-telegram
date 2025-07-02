.PHONY: install dev test lint format clean help run build up down logs shell restart status

# Default target
help:
	@echo "Available commands:"
	@echo "  install         - Install production dependencies"
	@echo "  dev             - Install development dependencies"
	@echo "  test            - Run tests"
	@echo "  lint            - Run linting checks"
	@echo "  format          - Format code"
	@echo "  clean           - Clean up generated files"
	@echo "  run             - Run the bot (blocking)"
	@echo "  run-debug       - Run the bot with debug logging (blocking)"
	@echo ""
	@echo "Docker commands:"
	@echo "  build           - Build Docker image"
	@echo "  up              - Start bot in background with Docker Compose"
	@echo "  down            - Stop and remove Docker containers"
	@echo "  logs            - View bot logs"
	@echo "  shell           - Open shell in running container"
	@echo "  restart         - Restart bot (useful for config changes)"
	@echo "  status          - View container status"

install:
	poetry install --only=main

dev:
	poetry install
	poetry run pre-commit install --install-hooks || echo "pre-commit not configured yet"

test:
	poetry run pytest

lint:
	poetry run black --check src tests
	poetry run isort --check-only src tests
	poetry run flake8 src tests
	poetry run mypy src

format:
	poetry run black src tests
	poetry run isort src tests

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ .pytest_cache/ dist/ build/

run:
	poetry run claude-telegram-bot

# For debugging
run-debug:
	poetry run claude-telegram-bot --debug

# Docker commands
build:
	docker build -t claude-telegram-bot .

up:
	@echo "Starting Claude Telegram Bot in background..."
	@mkdir -p data
	docker compose up -d
	@echo "Bot started! Use 'make logs' to view logs."

down:
	docker compose down

logs:
	docker compose logs -f claude-telegram-bot

shell:
	docker compose exec claude-telegram-bot /bin/bash

# Restart bot (useful for config changes)
restart:
	docker compose restart claude-telegram-bot

# View status
status:
	docker compose ps