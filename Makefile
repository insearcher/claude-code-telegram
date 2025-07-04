.PHONY: install dev test lint format clean help run run-debug run-clip run-debug-clip run-log build up down logs shell restart status

# Default target
help:
	@echo "Available commands:"
	@echo "  install         - Install production dependencies"
	@echo "  dev             - Install development dependencies"
	@echo "  test            - Run tests"
	@echo "  lint            - Run linting checks"
	@echo "  format          - Format code"
	@echo "  clean           - Clean up generated files"
	@echo ""
	@echo "Run commands:"
	@echo "  run             - Run the bot (blocking)"
	@echo "  run-debug       - Run the bot with debug logging (blocking)"
	@echo "  run-clip        - Run bot and copy logs to clipboard on exit (macOS)"
	@echo "  run-debug-clip  - Run bot in debug mode and copy logs to clipboard (macOS)"
	@echo "  run-log         - Run bot and save logs to timestamped file"
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

# Run with logs copied to clipboard (macOS)
run-clip:
	@echo "Starting bot with clipboard logging..."
	@echo "Press Ctrl+C to stop and copy logs to clipboard"
	@poetry run claude-telegram-bot 2>&1 | tee /tmp/claude-bot.log; \
	cat /tmp/claude-bot.log | pbcopy && \
	echo "\n✅ Logs copied to clipboard!"

# Run in debug mode with logs copied to clipboard (macOS)
run-debug-clip:
	@echo "Starting bot in debug mode with clipboard logging..."
	@echo "Press Ctrl+C to stop and copy logs to clipboard"
	@poetry run claude-telegram-bot --debug 2>&1 | tee /tmp/claude-bot-debug.log; \
	cat /tmp/claude-bot-debug.log | pbcopy && \
	echo "\n✅ Debug logs copied to clipboard!"

# Run with logs saved to file
run-log:
	@mkdir -p logs
	@echo "Starting bot with file logging..."
	@echo "Logs will be saved to logs/bot-$$(date +%Y%m%d-%H%M%S).log"
	@poetry run claude-telegram-bot 2>&1 | tee "logs/bot-$$(date +%Y%m%d-%H%M%S).log"

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