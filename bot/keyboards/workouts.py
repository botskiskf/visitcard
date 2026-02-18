from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def workouts_start_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Для новичков", callback_data="workouts:beginner"),
    )
    builder.row(
        InlineKeyboardButton(text="План на неделю", callback_data="workouts:plans"),
        InlineKeyboardButton(text="Все программы", callback_data="workouts:programs"),
    )
    builder.row(InlineKeyboardButton(text="« В главное меню", callback_data="main"))
    return builder.as_markup()


def beginner_blocks_kb(block_ids: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    titles = {"block1": "Блок 1", "block2": "Блок 2", "block3": "Блок 3", "block4": "Блок 4"}
    for bid in block_ids:
        builder.row(
            InlineKeyboardButton(
                text=titles.get(bid, bid),
                callback_data=f"beginner:{bid}",
            )
        )
    builder.row(InlineKeyboardButton(text="« Назад", callback_data="workouts"))
    return builder.as_markup()


def beginner_exercises_kb(block_id: str, exercises: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, ex in enumerate(exercises):
        builder.row(
            InlineKeyboardButton(
                text=ex["title"],
                callback_data=f"beginner_exercise:{block_id}:{i}",
            )
        )
    builder.row(InlineKeyboardButton(text="« К блокам", callback_data="workouts:beginner"))
    return builder.as_markup()


def beginner_exercise_card_kb(block_id: str, current_index: int, total: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Записать вес", callback_data=f"logweight:{block_id}:{current_index}"),
    )
    if total > 1:
        prev_i = (current_index - 1) % total
        next_i = (current_index + 1) % total
        builder.row(
            InlineKeyboardButton(
                text="« Предыдущее",
                callback_data=f"beginner_exercise:{block_id}:{prev_i}",
            ),
            InlineKeyboardButton(
                text="Следующее »",
                callback_data=f"beginner_exercise:{block_id}:{next_i}",
            ),
        )
    builder.row(
        InlineKeyboardButton(text="« К списку упражнений", callback_data=f"beginner:{block_id}"),
    )
    return builder.as_markup()


def plans_list_kb(plans: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in plans:
        builder.row(
            InlineKeyboardButton(text=p["title"], callback_data=f"plan:{p['id']}"),
        )
    builder.row(InlineKeyboardButton(text="« Назад", callback_data="workouts"))
    return builder.as_markup()


def plan_days_kb(plan_id: str, days: list, program_titles: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for d in days:
        program_title = program_titles.get(d["program_id"], d["program_id"])
        builder.row(
            InlineKeyboardButton(
                text=f"{d['day']} — {program_title}",
                callback_data=f"planday:{plan_id}:{d['program_id']}",
            )
        )
    builder.row(InlineKeyboardButton(text="« К планам", callback_data="workouts:plans"))
    return builder.as_markup()


def programs_kb(programs: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in programs:
        builder.row(
            InlineKeyboardButton(
                text=p["title"],
                callback_data=f"program:{p['id']}",
            )
        )
    builder.row(InlineKeyboardButton(text="« Назад", callback_data="workouts"))
    return builder.as_markup()


def exercises_kb(program_id: str, exercises: list, current_index: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, ex in enumerate(exercises):
        builder.row(
            InlineKeyboardButton(
                text=ex["title"],
                callback_data=f"exercise:{program_id}:{i}",
            )
        )
    builder.row(
        InlineKeyboardButton(text="« К программам", callback_data="workouts"),
    )
    return builder.as_markup()


def exercise_card_kb(program_id: str, current_index: int, total: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if total > 1:
        prev_i = (current_index - 1) % total
        next_i = (current_index + 1) % total
        builder.row(
            InlineKeyboardButton(
                text="« Предыдущее",
                callback_data=f"exercise:{program_id}:{prev_i}",
            ),
            InlineKeyboardButton(
                text="Следующее »",
                callback_data=f"exercise:{program_id}:{next_i}",
            ),
        )
    builder.row(
        InlineKeyboardButton(text="« К списку упражнений", callback_data=f"program:{program_id}"),
    )
    return builder.as_markup()
