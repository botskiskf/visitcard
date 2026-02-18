import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN, BASE_DIR
from bot.storage.db import init_db
from bot.handlers import start
from bot.handlers import workouts, progress

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    (BASE_DIR / "data").mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "assets" / "images" / "workouts").mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "assets" / "images" / "exercises").mkdir(parents=True, exist_ok=True)
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(workouts.router)
    dp.include_router(progress.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
