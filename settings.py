import os
from dotenv import load_dotenv

load_dotenv()


def _parse_status_messages(raw_value):
    if not raw_value:
        return []

    # Use || as delimiter so status text can still contain commas.
    return [segment.strip() for segment in raw_value.split("||") if segment.strip()]

# The prefix that will be used to parse commands.
# It doesn't have to be a single character!
COMMAND_PREFIX = os.environ.get('COMMAND_PREFIX', '.')

# The bot token. Keep this secret!
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# The now playing game. Set this to anything false-y ("", None) to disable it
NOW_PLAYING = os.environ.get('NOW_PLAYING', COMMAND_PREFIX + "commands")

# Optional rotating statuses.
# Format per entry: "type:text" and separate multiple entries with "||".
# Supported types: playing, listening, watching, competing.
# Placeholders available in text: {prefix}, {server_members}.
STATUS_MESSAGES = _parse_status_messages(os.environ.get('STATUS_MESSAGES'))
STATUS_ROTATION_INTERVAL_SECONDS = int(
    os.environ.get('STATUS_ROTATION_INTERVAL_SECONDS', '45')
)

# Base directory. Feel free to use it if you want.
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
