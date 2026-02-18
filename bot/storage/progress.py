from datetime import datetime
from typing import List, Tuple, Any

import aiosqlite

from bot.config import DB_PATH


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


async def add_weight(user_id: int, value: float) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO progress_weight (user_id, value, recorded_at) VALUES (?, ?, ?)",
            (user_id, value, _now()),
        )
        await db.commit()


async def add_measurement(user_id: int, name: str, value: float, unit: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO progress_measurements (user_id, name, value, unit, recorded_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, name, value, unit, _now()),
        )
        await db.commit()


async def add_achievement(user_id: int, text: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO progress_achievements (user_id, text, recorded_at) VALUES (?, ?, ?)",
            (user_id, text, _now()),
        )
        await db.commit()


async def get_weight_history(user_id: int, limit: int = 20) -> List[Tuple[float, str]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT value, recorded_at FROM progress_weight WHERE user_id = ? ORDER BY recorded_at DESC LIMIT ?",
            (user_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
        return [(r["value"], r["recorded_at"]) for r in rows]


async def get_measurements_history(
    user_id: int, limit: int = 20
) -> List[Tuple[str, float, str, str]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT name, value, unit, recorded_at FROM progress_measurements WHERE user_id = ? ORDER BY recorded_at DESC LIMIT ?",
            (user_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
        return [(r["name"], r["value"], r["unit"], r["recorded_at"]) for r in rows]


async def get_achievements_history(
    user_id: int, limit: int = 20
) -> List[Tuple[str, str]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT text, recorded_at FROM progress_achievements WHERE user_id = ? ORDER BY recorded_at DESC LIMIT ?",
            (user_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
        return [(r["text"], r["recorded_at"]) for r in rows]


async def get_exercise_last_weight(user_id: int, exercise_key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT weight FROM user_exercise_weights WHERE user_id = ? AND exercise_key = ? ORDER BY recorded_at DESC LIMIT 1",
            (user_id, exercise_key),
        ) as cursor:
            row = await cursor.fetchone()
        return float(row["weight"]) if row else None


async def set_exercise_weight(user_id: int, exercise_key: str, weight: float) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO user_exercise_weights (user_id, exercise_key, weight, recorded_at) VALUES (?, ?, ?, ?)",
            (user_id, exercise_key, weight, _now()),
        )
        await db.commit()
