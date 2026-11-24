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

- `your_bot.py`: Main bot startup, Discord client events, scheduler bootstrap, and keep-alive startup.
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

The GCash command converts USD prices to PHP using ExchangeRate.fun's hourly USD/PHP market rate. It refreshes the rate at most once per hour when the command is used and shows the source timestamp in the overview. If a refresh fails, it uses the last rate fetched by the running bot and marks it as last available. If no rate has been fetched yet, the command asks users to try again later instead of showing an outdated PHP amount.

## Environment Variables

Create a `.env` file (or set env vars directly):

- `BOT_TOKEN` (required): Discord bot token.
- `COMMAND_PREFIX` (optional, default: `.`): Command prefix.
- `NOW_PLAYING` (optional, default: `<prefix>commands`): Presence game text.
- `STATUS_MESSAGES` (optional): Rotating statuses, separated by `||`, format `type:text`.
- `STATUS_PRESENCES` (optional, default: `online`): Rotating presence indicators, separated by `||`. Use `online`, `idle`, and/or `dnd`.
- `STATUS_ROTATION_INTERVAL_SECONDS` (optional, default: `45`): Seconds between activity text changes (minimum 10).
- `STATUS_PRESENCE_INTERVAL_HOURS` (optional, default: `4`): Hours between online, idle, and DND changes.
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

### Local `.env`

Copy `.env.example` to `.env` if needed, then add your Discord bot token to `BOT_TOKEN`. The local `.env` file is ignored by Git.

```env
BOT_TOKEN=your_discord_bot_token
COMMAND_PREFIX=.
NOW_PLAYING=.commands
STATUS_MESSAGES=playing:{prefix}help||playing:helping {server_members} members||listening:beautiful people
STATUS_PRESENCES=online||idle||dnd
STATUS_ROTATION_INTERVAL_SECONDS=45
STATUS_PRESENCE_INTERVAL_HOURS=4
PORT=8080
POPCAT_BASE_URL=https://api.popcat.xyz
```

The image generator command now uses Popcat API endpoints that are avatar/image friendly:

- `achievement` (custom text), `ad`, `blur`, `clown`, `colorify`, `drip`, `greyscale`, `gun`
- `huerotate`/`hue-rotate`, `invert`, `jail`, `jokeoverhead`, `mnm`, `nokia`, `pet`
- `sadcat`, `ship`, `uncover`, `wanted`

Usage examples:

- `.gen wanted @user`
- `.gen achievement Built a castle`
- `.gen ad https://example.com/image.png`
- `.ship @user1 @user2`

## Setup

1. Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

If `venv` is unavailable but `virtualenv` is installed, use `python3 -m virtualenv .venv` for the first command.

2. Fill in `BOT_TOKEN` in `.env`, then run the bot:

```bash
./start.sh
```

### Run with PM2

From the project directory, register the script with PM2 and save the process list:

```bash
pm2 start ./start.sh --name bryxel-bot --interpreter bash --restart-delay 5000
pm2 save
```

To restore saved PM2 processes after a machine reboot, run `pm2 startup` as your normal user, then run the `sudo` command it prints. PM2 manages the bot process; `pm2 logs bryxel-bot` shows its output.

### Keep-alive endpoint

The bot serves `GET /` and `GET /ping` on port `8080` by default. Check it locally at `http://127.0.0.1:8080/ping`.

### Development auto-restart

If the bot is not running under PM2, use `.venv/bin/python auto_restart.py` to restart it when Python files change. Do not run both launch methods at once, or you will start two bot processes.

## Notes

- Command modules are auto-imported recursively from `commands/`.
- The event scheduler is wired in `your_bot.py`, but no concrete custom events are currently present in `events/`.
- If `BOT_TOKEN` is missing, startup will fail fast with a configuration error.

## License

GPL-3.0
