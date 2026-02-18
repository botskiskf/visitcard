from datetime import datetime
from typing import Optional

import aiosqlite

from bot.config import DB_PATH


async def get_or_create_user(
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
        if row:
            return row["id"]
        now = datetime.utcnow().isoformat() + "Z"
        await db.execute(
            "INSERT INTO users (telegram_id, username, first_name, created_at) VALUES (?, ?, ?, ?)",
            (telegram_id, username or "", first_name or "", now),
        )
        await db.commit()
        async with db.execute("SELECT last_insert_rowid() as id") as cursor:
            row = await cursor.fetchone()
        return row["id"]
