import os
from dotenv import load_dotenv

load_dotenv()


def _parse_status_messages(raw_value):
    if not raw_value:
        return []

    # Use || as delimiter so status text can still contain commas.
    return [segment.strip() for segment in raw_value.split("||") if segment.strip()]


def _parse_presence_statuses(raw_value):
    statuses = [status.lower() for status in _parse_status_messages(raw_value)]
    invalid = [status for status in statuses if status not in {"online", "idle", "dnd"}]
    if invalid:
        raise ValueError(f"Unsupported STATUS_PRESENCES value: {', '.join(invalid)}")
    return statuses or ["online"]

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
STATUS_PRESENCES = _parse_presence_statuses(os.environ.get('STATUS_PRESENCES'))
STATUS_ROTATION_INTERVAL_SECONDS = int(
    os.environ.get('STATUS_ROTATION_INTERVAL_SECONDS', '45')
)
STATUS_PRESENCE_INTERVAL_HOURS = float(
    os.environ.get('STATUS_PRESENCE_INTERVAL_HOURS', '4')
)
if STATUS_PRESENCE_INTERVAL_HOURS <= 0:
    raise ValueError("STATUS_PRESENCE_INTERVAL_HOURS must be greater than zero")

# Base directory. Feel free to use it if you want.
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
