# Docker Quick Start

Fastest way to run the Claude Telegram Bot in the background using Docker.

## Prerequisites

- Docker and Docker Compose installed
- **Claude Code CLI installed and authenticated** (`claude auth login`)
- Telegram bot token from [@BotFather](https://t.me/botfather)
- Your Telegram user ID (get from [@userinfobot](https://t.me/userinfobot))
- **OpenAI API key** for voice transcription (get from [OpenAI Platform](https://platform.openai.com/api-keys))

## Quick Setup

1. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings:
   # - TELEGRAM_BOT_TOKEN=your_bot_token
   # - TELEGRAM_BOT_USERNAME=your_bot_username  
   # - ALLOWED_USERS=your_telegram_user_id
   # - APPROVED_DIRECTORY=/app/projects  # This maps to your mounted projects
   # - ANTHROPIC_API_KEY=  # Leave empty for Claude Code Max subscription
   # - OPENAI_API_KEY=your_openai_api_key  # Required for voice transcription
   ```

2. **Update docker-compose.yml** - Edit the projects volume mount:
   ```yaml
   volumes:
     # Change this path to your actual projects directory
     - /Users/your_username/projects:/app/projects:ro
   ```

3. **Start the bot**:
   ```bash
   make up
   ```

4. **View logs**:
   ```bash
   make logs
   ```

## Management Commands

```bash
make status                 # Check if bot is running
make restart                # Restart after config changes
make down                   # Stop the bot
make shell                  # Debug shell into container
```

## Data Persistence

- Bot database is stored in `./data/bot.db`
- Logs are managed by Docker with automatic rotation
- Configuration is mounted read-only from `.env`

## Troubleshooting

**Bot won't start**: Check logs with `make logs`

**Permission errors**: Ensure mounted directories are readable

**Config changes**: Run `make restart` after editing `.env`

**Database issues**: Delete `./data/bot.db` to reset (loses history)