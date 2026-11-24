#!/usr/bin/env bash
set -euo pipefail

bot_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
bot_python="$bot_dir/.venv/bin/python"

if [[ ! -x "$bot_python" ]]; then
    echo "Missing virtual environment. Install dependencies in $bot_dir/.venv first." >&2
    exit 1
fi

cd "$bot_dir"
exec "$bot_python" your_bot.py
