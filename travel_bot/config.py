"""API keys and bot configuration from .env."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from travel_bot directory or current working directory
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEFAULT_ORIGIN_AIRPORT = os.getenv("DEFAULT_ORIGIN_AIRPORT", "BRU")
CURRENCY = os.getenv("CURRENCY", "EUR")

# Optional: comma-separated Telegram user IDs for personal-use restriction (empty = allow all)
_allowed = os.getenv("ALLOWED_TELEGRAM_IDS", "").strip()
ALLOWED_TELEGRAM_IDS = [int(x.strip()) for x in _allowed.split(",") if x.strip()]
