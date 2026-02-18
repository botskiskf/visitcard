from aiogram import Router, F
from aiogram.types import Message

from bot.keyboards.main import get_main_menu_kb
from bot.storage.user import get_or_create_user

router = Router(name="start")


@router.message(F.text == "/start")
async def cmd_start(message: Message) -> None:
    if message.from_user:
        await get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
    name = message.from_user.first_name or "друг" if message.from_user else "друг"
    await message.answer(
        f"Привет, {name}!\n\n"
        "Я фитнес-бот: помогу с программами тренировок и отслеживанием прогресса.\n\n"
        "Выбери раздел:",
        reply_markup=get_main_menu_kb(),
    )
