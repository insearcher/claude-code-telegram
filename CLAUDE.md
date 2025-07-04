# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Claude Code Telegram Bot that provides remote access to Claude Code through Telegram, enabling developers to interact with their projects from anywhere. The bot acts as a bridge between Telegram and Claude Code, offering terminal-like interface with directory navigation, file management, and full Claude AI assistance.

## Development Commands

### Environment Setup
```bash
make dev                    # Install development dependencies and setup pre-commit hooks
```

### Running the Bot

**Local Development (Blocking)**:
```bash
make run                    # Run the bot in production mode
make run-debug              # Run the bot with debug logging enabled
make run-clip               # Run bot and copy logs to clipboard on exit (macOS)
make run-debug-clip         # Run bot in debug mode and copy logs to clipboard (macOS)
make run-log                # Run bot and save logs to timestamped file in logs/
```

**IMPORTANT**: All run commands are **blocking operations** that start the bot in polling mode and will not return control to the terminal. The bot runs continuously waiting for Telegram messages. Use Ctrl+C to stop the bot.

**Clipboard Commands** (`run-clip`, `run-debug-clip`):
- macOS only (uses `pbcopy`)
- Logs are automatically copied to clipboard when you stop the bot with Ctrl+C
- Useful for quickly sharing logs when reporting issues

**Docker (Background)**:
```bash
make build                  # Build Docker image
make up                     # Start bot in background with Docker Compose
make logs                   # View real-time logs
make down                   # Stop and remove containers
make restart                # Restart bot (useful for config changes)
make status                 # View container status
make shell                  # Open shell in running container
```

**IMPORTANT**: For Docker deployment with Claude Code Max subscription:
1. **Authenticate Claude CLI locally**: `claude auth login` 
2. **Leave `ANTHROPIC_API_KEY` empty** - the bot will use your CLI authentication
3. **Provide `OPENAI_API_KEY`** for voice transcription feature
4. The Docker container will mount your `~/.config/claude` for authentication

For production deployment, Docker is recommended as it runs the bot in the background and provides automatic restarts on failure.

### Testing and Code Quality
```bash
make test                   # Run all tests with pytest
make lint                   # Run all linting checks (black, isort, flake8, mypy)
make format                 # Auto-format code with black and isort
make clean                  # Clean up generated files and caches
```

### Single Test Execution
```bash
poetry run pytest tests/unit/test_specific_file.py  # Run specific test file
poetry run pytest tests/unit/test_file.py::TestClass::test_method  # Run specific test method
poetry run pytest -k "test_name_pattern"  # Run tests matching pattern
```

## Architecture Overview

### Core Components

**Bot Layer (`src/bot/`)**
- `core.py`: Main bot application with Telegram integration and global error handling
- `handlers/`: Message, command, and callback handlers for different user interactions
- `middleware/`: Authentication, rate limiting, and security layers
- `features/`: Modular features like git integration, file handling, quick actions
- `utils/formatting.py`: Telegram message formatting with Markdown/HTML fallback system

**Claude Integration (`src/claude/`)**
- `facade.py`: Main interface for Claude operations with dual SDK/CLI support
- `sdk_integration.py`: Direct Anthropic Python SDK integration
- `integration.py`: Claude CLI subprocess management (legacy/fallback mode)
- `session.py`: Session management with persistence and cost tracking
- `monitor.py`: Usage monitoring and cost control

**Configuration System (`src/config/`)**
- `settings.py`: Pydantic-based configuration with validation and type safety
- `loader.py`: Environment-aware configuration loading with overrides
- `environments.py`: Environment-specific settings (development/testing/production)

**Storage Layer (`src/storage/`)**
- `database.py`: SQLite database management with connection pooling and migrations
- `models.py`: Dataclass models for users, sessions, messages, audit logs
- `facade.py`: High-level storage operations and business logic
- `session_storage.py`: Persistent session storage replacing in-memory storage

**Security (`src/security/`)**
- `auth.py`: Multi-layer authentication (whitelist + optional token-based)
- `validators.py`: Input validation and path security
- `rate_limiter.py`: Token bucket rate limiting with cost-based controls
- `audit.py`: Comprehensive audit logging for security events

### Key Design Patterns

**Dual Integration Mode**: The bot supports both Anthropic Python SDK and Claude CLI subprocess modes, controlled by `USE_SDK` setting. SDK mode is preferred for production.

**Message Formatting**: Advanced Telegram message formatting with automatic fallback from Markdown to HTML to plain text when parsing fails.

**Feature Registry**: Modular feature system where features can be enabled/disabled and are automatically registered.

**Layered Security**: Multiple security layers including authentication middleware, path validation, rate limiting, and comprehensive audit logging.

**Session Persistence**: Full conversation context preservation using SQLite with proper cleanup and cost tracking.

## Docker Deployment

The project includes complete Docker configuration for containerized deployment:

**Files**:
- `Dockerfile`: Multi-stage build with Python 3.11 slim, Poetry, and security hardening
- `docker-compose.yml`: Production-ready compose configuration with health checks, resource limits, and volume mounts
- `.dockerignore`: Optimized for smaller build contexts

**Key Features**:
- Non-root user execution for security
- Automatic restarts on failure
- Health checks for container monitoring
- Persistent data volumes for SQLite database
- Resource limits to prevent resource exhaustion
- Structured logging with rotation

**Volume Mounts**:
- `.env` file for configuration (read-only)
- `./data` for SQLite database persistence
- Projects directory (configurable path) for file access

## Configuration

The bot uses environment-based configuration with `.env` files. Key configuration areas:

**Required Settings**:
- `TELEGRAM_BOT_TOKEN`: Bot token from @BotFather
- `TELEGRAM_BOT_USERNAME`: Bot username (without @)
- `APPROVED_DIRECTORY`: Base directory for project access (security boundary)
- `ALLOWED_USERS`: Comma-separated list of allowed Telegram user IDs

**Claude Integration**:
- `USE_SDK=true`: Use Python SDK (recommended) vs CLI subprocess
- `ANTHROPIC_API_KEY`: API key for SDK mode (optional if Claude CLI is authenticated)
- `CLAUDE_ALLOWED_TOOLS`: Comma-separated list of allowed Claude tools

**Voice Message Support**:
- `OPENAI_API_KEY`: OpenAI API key for Whisper voice transcription
- `VOICE_ENABLED=true`: Enable voice message processing
- `VOICE_MAX_DURATION=1800`: Maximum voice duration in seconds (30 minutes)
- `VOICE_MAX_FILE_SIZE=104857600`: Maximum voice file size in bytes (100MB)
- `WHISPER_LANGUAGE=ru`: Language for Whisper transcription (ru, en, auto)

**Personal Claude Code Max Configuration**:
This bot is configured for personal use with generous limits:
- `CLAUDE_MAX_COST_PER_USER=999999.0`: Effectively unlimited cost
- `CLAUDE_MAX_TURNS=100`: Long conversations supported
- `CLAUDE_TIMEOUT_SECONDS=1200`: 20-minute timeout for complex operations
- `RATE_LIMIT_REQUESTS=1000`: Very high request limits
- `SESSION_TIMEOUT_HOURS=48`: 2-day session persistence
- `MAX_SESSIONS_PER_USER=20`: Multiple parallel projects
- `MAX_FILE_UPLOAD_SIZE_MB=500`: Large file support

## Database Schema

The bot uses SQLite with comprehensive schema including:
- `users`: User management and usage tracking
- `sessions`: Claude conversation sessions with cost tracking
- `messages`: Full message history with prompts and responses
- `tool_usage`: Tool execution tracking
- `audit_log`: Security events and user actions
- `cost_tracking`: Daily usage and cost limits

Database migrations are handled automatically on startup.

## Known Limitations

**Stop Button**: The Stop button only works when using Claude CLI subprocess mode (`USE_SDK=false`). In SDK mode, the button provides visual feedback but cannot actually interrupt the execution. This is due to the synchronous nature of the SDK integration.

**Concurrent Requests**: The bot processes requests sequentially. While Claude is processing, other commands (including Stop) are queued and processed after completion.

## Security Considerations

**Directory Isolation**: All operations are confined to `APPROVED_DIRECTORY` with strict path validation to prevent directory traversal attacks.

**Authentication**: Whitelist-based user authentication with optional token-based secondary authentication.

**Rate Limiting**: Advanced rate limiting with both request-based and cost-based limits using token bucket algorithm.

**Audit Logging**: Comprehensive logging of all user actions, security violations, and system events.

**Data Privacy**: All user prompts, responses, and file contents are stored locally in SQLite and transmitted to Telegram and Anthropic APIs.

## Testing Architecture

Tests are organized in `tests/unit/` with structure mirroring `src/`:
- `test_bot/`: Bot functionality tests
- `test_claude/`: Claude integration tests
- `test_security/`: Security component tests
- `test_storage/`: Database and storage tests
- `test_config.py`: Configuration system tests

Uses pytest with async support, coverage reporting, and mock objects for external dependencies.