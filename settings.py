import os
from dotenv import load_dotenv

load_dotenv()

# The prefix that will be used to parse commands.
# It doesn't have to be a single character!
COMMAND_PREFIX = os.environ.get('COMMAND_PREFIX', '.')

# The bot token. Keep this secret!
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# The now playing game. Set this to anything false-y ("", None) to disable it
NOW_PLAYING = os.environ.get('NOW_PLAYING', COMMAND_PREFIX + "commands")

# Base directory. Feel free to use it if you want.
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
