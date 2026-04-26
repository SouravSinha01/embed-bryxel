# Bryxel Assistant (Discord Bot)

Bryxel Assistant is a modular Discord bot for the BryxelRealm community.
It includes categorized commands, rich embeds, interactive views/buttons, a keep-alive web endpoint, and an optional auto-restart script for development.

## Features

- Modular command loading from the `commands/` package.
- Command categories (`Bot`, `Ingame`, `Utility`) used by the help system.
- Interactive help center with dropdown navigation.
- Utility commands for voting, donation/store links, server IP info, tickets, polls, and avatars.
- Ingame command guide embeds with dropdown-based navigation.
- Keep-alive Flask server with `/` and `/ping` endpoints.
- Optional watchdog-based auto-restart while editing Python files.

## Project Structure

- `your_bot.py`: Main bot startup, Discord client events, scheduler bootstrap, keep-alive startup.
- `message_handler.py`: Registers command handlers from subclasses of `BaseCommand` and dispatches commands.
- `settings.py`: Environment-based runtime configuration.
- `keep_alive.py`: Flask app used for health checks.
- `auto_restart.py`: Development helper that restarts the bot when Python files change.
- `commands/`: Command modules grouped into subpackages.
- `events/`: Event base system (currently no custom scheduled events are defined).

## Commands

Prefix defaults to `.` (configurable via `COMMAND_PREFIX`).

### Bot

- `.commands` (aliases: `.help`, `.h`)
  - Interactive help center with category and per-command views.
- `.ping` (aliases: `.pong`, `.latency`)
  - Bot latency and runtime stats.
  - Optional Minecraft server check with host/port (for example: `.ping example.com 25565`).

### Ingame

- `.igm` (alias: `.ingame`)
  - Ingame command guide with dropdown details for server-specific commands.
- `.code` (aliases: `.colorcode`, `.color`)
  - Minecraft color/format code reference embed.

### Utility

- `.ip` (aliases: `.serverip`, `.address`)
  - Shows BryxelRealm host, direct IP, and live status via `mcstatus`.
- `.avatar <user>` (alias: `.av`)
  - Shows a mentioned user's avatar (or accepts a user ID).
- `.donate` (aliases: `.store`, `.shop`, `.website`, `.site`)
  - Sends webshop and website links with action buttons.
- `.poll Question | Option 1 | Option 2 [| duration=10m]`
  - Interactive poll with vote buttons and optional duration.
- `.ticket` (alias: `.guide`)
  - Paged ticket-opening guide with navigation buttons.
- `.vote` (aliases include `.voting`, `.votes`, `.v`)
  - Voting links to support BryxelRealm.

## Environment Variables

Create a `.env` file (or set env vars directly):

- `BOT_TOKEN` (required): Discord bot token.
- `COMMAND_PREFIX` (optional, default: `.`): Command prefix.
- `NOW_PLAYING` (optional, default: `<prefix>commands`): Presence game text.
- `STATUS_MESSAGES` (optional): Rotating statuses, separated by `||`, format `type:text`.
- `STATUS_ROTATION_INTERVAL_SECONDS` (optional, default: `45`): Rotation interval.
- `PORT` (optional, default: `8080`): Port used by the Flask keep-alive service.
- `POPCAT_BASE_URL` (optional, default: `https://api.popcat.xyz`): Base URL for Popcat API.

Supported status types:

- `playing`
- `listening`
- `watching`
- `competing`

Supported placeholders inside status text:

- `{prefix}`
- `{server_members}`

### Example `.env`

```env
BOT_TOKEN=your_discord_bot_token
COMMAND_PREFIX=.
NOW_PLAYING=.commands
STATUS_MESSAGES=playing:{prefix}help||playing:helping {server_members} members||listening:beautiful people
STATUS_ROTATION_INTERVAL_SECONDS=45
PORT=8080
POPCAT_BASE_URL=https://api.popcat.xyz
```

The image generator command now uses Popcat API endpoints that are avatar/image friendly:

- `ad`, `blur`, `clown`, `colorify`, `communism`, `drip`, `greyscale`, `gun`
- `huerotate`/`hue-rotate`, `invert`, `jail`, `jokeoverhead`, `mnm`, `nokia`, `pet`
- `sadcat`, `ship`, `uncover`, `wanted`

Usage examples:

- `.gen wanted @user`
- `.gen ad https://example.com/image.png`
- `.ship @user1 @user2`

## Setup

1. Create/activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the bot:

```bash
python your_bot.py
```

## Keep-Alive Endpoints

When running, the bot also starts a Flask server:

- `GET /` -> `Bot is alive!`
- `GET /ping` -> JSON status payload

Example local check:

- `http://127.0.0.1:8080/ping`

## Development Auto-Restart

For local development, you can run:

```bash
python auto_restart.py
```

This script watches for `.py` file changes and restarts `your_bot.py` automatically.

## Notes

- Command modules are auto-imported recursively from `commands/`.
- The event scheduler is wired in `your_bot.py`, but no concrete custom events are currently present in `events/`.
- If `BOT_TOKEN` is missing, startup will fail fast with a configuration error.

## License

GPL-3.0
