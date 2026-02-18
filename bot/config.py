import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_raw = os.getenv("BOT_TOKEN")
BOT_TOKEN = _raw.strip() if _raw else ""
if not BOT_TOKEN or "your_bot_token" in BOT_TOKEN.lower() or "botfather" in BOT_TOKEN.lower():
    raise ValueError(
        "BOT_TOKEN не задан или это заглушка. "
        "Получи токен у @BotFather в Telegram и впиши в файл .env одну строку: BOT_TOKEN=твой_токен"
    )

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "fitness.db"
DATA_DIR = BASE_DIR / "bot" / "data"
ASSETS_DIR = BASE_DIR / "assets" / "images"
