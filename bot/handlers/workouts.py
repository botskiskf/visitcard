import json
from pathlib import Path
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.config import DATA_DIR, ASSETS_DIR
from bot.keyboards.workouts import (
    workouts_start_kb,
    plans_list_kb,
    plan_days_kb,
    programs_kb,
    exercises_kb,
    exercise_card_kb,
    beginner_blocks_kb,
    beginner_exercises_kb,
    beginner_exercise_card_kb,
)
from bot.keyboards.main import get_main_menu_kb
from bot.storage import get_or_create_user, get_exercise_last_weight, set_exercise_weight

router = Router(name="workouts")


class ExerciseWeightState(StatesGroup):
    waiting_weight = State()


PROGRAMS_PATH = DATA_DIR / "programs.json"
PLANS_PATH = DATA_DIR / "plans.json"
PLACEHOLDER_PATH = ASSETS_DIR / "placeholder.png"


def _load_programs() -> list:
    if not PROGRAMS_PATH.exists():
        return []
    with open(PROGRAMS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_plans() -> list:
    if not PLANS_PATH.exists():
        return []
    with open(PLANS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_image_path(folder: str, slug: str) -> Optional[Path]:
    if not slug:
        return None
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        p = ASSETS_DIR / folder / f"{slug}{ext}"
        if p.exists():
            return p
    return None


def _get_photo(folder: str, slug: str):
    path = _get_image_path(folder, slug)
    if path:
        return FSInputFile(path)
    if PLACEHOLDER_PATH.exists():
        return FSInputFile(PLACEHOLDER_PATH)
    return None


BEGINNER_BLOCKS = ("block1", "block2", "block3", "block4")


@router.message(F.text == "Тренировки")
async def show_workouts_start(message: Message) -> None:
    await message.answer(
        "Тренировки: для новичков — 4 блока с записью веса, или план на неделю и все программы.",
        reply_markup=workouts_start_kb(),
    )


@router.callback_query(F.data == "workouts")
async def callback_workouts_back(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(
        "Тренировки: для новичков — 4 блока с записью веса, или план на неделю и все программы.",
        reply_markup=workouts_start_kb(),
    )


@router.callback_query(F.data == "workouts:beginner")
async def callback_beginner_blocks(callback: CallbackQuery) -> None:
    await callback.answer()
    programs = _load_programs()
    block_ids = [p["id"] for p in programs if p["id"] in BEGINNER_BLOCKS]
    if not block_ids:
        await callback.message.edit_text("Блоки для новичков пока не добавлены.")
        return
    await callback.message.edit_text(
        "Для новичков: 4 занятия в неделю, в каждом упражнении 4 подхода по 15 повторений. Можно записывать вес.",
        reply_markup=beginner_blocks_kb(block_ids),
    )


@router.callback_query(F.data.startswith("beginner:"))
async def callback_beginner_block_exercises(callback: CallbackQuery) -> None:
    await callback.answer()
    block_id = callback.data.removeprefix("beginner:")
    if block_id not in BEGINNER_BLOCKS:
        return
    programs = _load_programs()
    program = next((p for p in programs if p["id"] == block_id), None)
    if not program:
        await callback.message.edit_text("Блок не найден.")
        return
    exercises = program.get("exercises", [])
    if not exercises:
        await callback.message.edit_text("В этом блоке пока нет упражнений.")
        return
    titles = {"block1": "Блок 1", "block2": "Блок 2", "block3": "Блок 3", "block4": "Блок 4"}
    await callback.message.edit_text(
        f"{titles.get(block_id, block_id)}. Выбери упражнение (4 подхода по 15 повторений):",
        reply_markup=beginner_exercises_kb(block_id, exercises),
    )


def _beginner_exercise_text(ex: dict, last_weight: Optional[float]) -> str:
    desc = ex.get("description", "")
    parts = [f"<b>{ex['title']}</b>", "", "4 подхода по 15 повторений.", ""]
    if last_weight is not None:
        parts.append(f"Предыдущий вес: <b>{last_weight} кг</b>")
    else:
        parts.append("Предыдущий вес: —")
    parts.extend(["", desc])
    return "\n".join(parts)


@router.callback_query(F.data.startswith("beginner_exercise:"))
async def callback_beginner_exercise_card(callback: CallbackQuery) -> None:
    await callback.answer()
    parts = callback.data.removeprefix("beginner_exercise:").split(":")
    if len(parts) < 2:
        return
    block_id, idx_str = parts[0], parts[1]
    try:
        index = int(idx_str)
    except ValueError:
        return
    programs = _load_programs()
    program = next((p for p in programs if p["id"] == block_id), None)
    if not program or block_id not in BEGINNER_BLOCKS:
        await callback.message.edit_text("Блок не найден.")
        return
    exercises = program.get("exercises", [])
    if not exercises or index < 0 or index >= len(exercises):
        await callback.message.edit_text("Упражнение не найдено.")
        return
    ex = exercises[index]
    user_id = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )
    exercise_key = f"{block_id}_{ex['id']}"
    last_weight = await get_exercise_last_weight(user_id, exercise_key)
    text = _beginner_exercise_text(ex, last_weight)
    photo = _get_photo("exercises", ex.get("image_slug", ""))
    kb = beginner_exercise_card_kb(block_id, index, len(exercises))
    try:
        await callback.message.delete()
    except Exception:
        pass
    if photo:
        await callback.message.answer_photo(
            photo=photo,
            caption=text,
            parse_mode="HTML",
            reply_markup=kb,
        )
    else:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("logweight:"))
async def callback_log_weight_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    parts = callback.data.removeprefix("logweight:").split(":")
    if len(parts) < 2:
        return
    block_id, idx_str = parts[0], parts[1]
    try:
        index = int(idx_str)
    except ValueError:
        return
    await state.update_data(block_id=block_id, index=index)
    await state.set_state(ExerciseWeightState.waiting_weight)
    await callback.message.edit_text("Введи вес в кг (число, например: 25 или 32.5):")


@router.message(ExerciseWeightState.waiting_weight, F.text)
async def callback_log_weight_save(message: Message, state: FSMContext) -> None:
    try:
        value = float(message.text.replace(",", ".").strip())
        if value <= 0 or value > 500:
            await message.answer("Введи корректный вес (0–500 кг):")
            return
    except ValueError:
        await message.answer("Введи число, например: 25 или 32.5")
        return
    data = await state.get_data()
    block_id = data.get("block_id")
    index = data.get("index", 0)
    await state.clear()
    programs = _load_programs()
    program = next((p for p in programs if p["id"] == block_id), None)
    if not program or block_id not in BEGINNER_BLOCKS:
        await message.answer("Ошибка: блок не найден. Выбери упражнение заново.")
        return
    exercises = program.get("exercises", [])
    if not exercises or index < 0 or index >= len(exercises):
        await message.answer("Ошибка: упражнение не найдено.")
        return
    ex = exercises[index]
    exercise_key = f"{block_id}_{ex['id']}"
    user_id = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    await set_exercise_weight(user_id, exercise_key, value)
    await message.answer(f"Вес {value} кг сохранён. Предыдущий вес для этого упражнения теперь: {value} кг.")


@router.callback_query(F.data == "workouts:plans")
async def callback_show_plans(callback: CallbackQuery) -> None:
    await callback.answer()
    plans = _load_plans()
    if not plans:
        await callback.message.edit_text("Планы на неделю пока не добавлены.")
        return
    await callback.message.edit_text(
        "План тренировок на неделю:",
        reply_markup=plans_list_kb(plans),
    )


@router.callback_query(F.data.startswith("plan:"))
async def callback_show_plan_days(callback: CallbackQuery) -> None:
    await callback.answer()
    plan_id = callback.data.removeprefix("plan:")
    plans = _load_plans()
    plan = next((p for p in plans if p["id"] == plan_id), None)
    if not plan:
        await callback.message.edit_text("План не найден.")
        return
    programs = _load_programs()
    program_titles = {p["id"]: p["title"] for p in programs}
    text = f"<b>{plan['title']}</b>\n\n{plan.get('description', '')}"
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=plan_days_kb(plan_id, plan["days"], program_titles),
    )


@router.callback_query(F.data.startswith("planday:"))
async def callback_plan_day_program(callback: CallbackQuery) -> None:
    await callback.answer()
    parts = callback.data.removeprefix("planday:").split(":")
    if len(parts) < 2:
        return
    program_id = parts[1]
    programs = _load_programs()
    program = next((p for p in programs if p["id"] == program_id), None)
    if not program:
        await callback.message.edit_text("Программа не найдена.")
        return
    exercises = program.get("exercises", [])
    if not exercises:
        await callback.message.edit_text(
            f"В программе «{program['title']}» пока нет упражнений."
        )
        return
    text = f"Программа: {program['title']}\n\nВыбери упражнение:"
    await callback.message.edit_text(
        text,
        reply_markup=exercises_kb(program_id, exercises),
    )


@router.callback_query(F.data == "workouts:programs")
async def callback_show_programs(callback: CallbackQuery) -> None:
    await callback.answer()
    programs = _load_programs()
    if not programs:
        await callback.message.edit_text("Программы тренировок пока не добавлены.")
        return
    await callback.message.edit_text(
        "Выбери программу тренировок:",
        reply_markup=programs_kb(programs),
    )


@router.callback_query(F.data.startswith("program:"))
async def show_exercises(callback: CallbackQuery) -> None:
    await callback.answer()
    program_id = callback.data.removeprefix("program:")
    programs = _load_programs()
    program = next((p for p in programs if p["id"] == program_id), None)
    if not program:
        await callback.message.edit_text("Программа не найдена.")
        return
    exercises = program.get("exercises", [])
    if not exercises:
        await callback.message.edit_text(
            f"В программе «{program['title']}» пока нет упражнений."
        )
        return
    text = f"Программа: {program['title']}\n\nВыбери упражнение:"
    await callback.message.edit_text(
        text,
        reply_markup=exercises_kb(program_id, exercises),
    )


@router.callback_query(F.data.startswith("exercise:"))
async def show_exercise_card(callback: CallbackQuery) -> None:
    await callback.answer()
    parts = callback.data.removeprefix("exercise:").split(":")
    if len(parts) < 2:
        return
    program_id = parts[0]
    try:
        index = int(parts[1])
    except ValueError:
        return
    programs = _load_programs()
    program = next((p for p in programs if p["id"] == program_id), None)
    if not program:
        await callback.message.edit_text("Программа не найдена.")
        return
    exercises = program.get("exercises", [])
    if not exercises or index < 0 or index >= len(exercises):
        await callback.message.edit_text("Упражнение не найдено.")
        return
    ex = exercises[index]
    text = f"<b>{ex['title']}</b>\n\n{ex.get('description', '')}"
    photo = _get_photo("exercises", ex.get("image_slug", ""))
    kb = exercise_card_kb(program_id, index, len(exercises))
    try:
        await callback.message.delete()
    except Exception:
        pass
    if photo:
        await callback.message.answer_photo(
            photo=photo,
            caption=text,
            parse_mode="HTML",
            reply_markup=kb,
        )
    else:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "main")
async def back_to_main(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        "Выбери раздел:",
        reply_markup=get_main_menu_kb(),
    )
