from typing import List, Optional
from arielbot.domain.interfaces.repository import BotStatusRepository
from arielbot.infrastructure.database import DatabaseManager


class SqlBotStatusRepository(BotStatusRepository):
    def __init__(self, db: DatabaseManager):
        self._db = db

    async def get(self, bot_id: int, group_id: int) -> Optional[tuple]:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "SELECT push_active, bot_active FROM botStatus WHERE bot=? AND groupId=?",
                (bot_id, group_id),
            )
            return await cursor.fetchone()

    async def save(self, bot_id: int, group_id: int,
                   push_active: int, bot_active: int) -> None:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "INSERT INTO botStatus (bot, groupId, push_active, bot_active) VALUES (?, ?, ?, ?)",
                (bot_id, group_id, push_active, bot_active),
            )

    async def update_push(self, bot_id: int, group_id: int, active: int) -> None:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "UPDATE botStatus SET push_active=? WHERE bot=? AND groupId=?",
                (active, bot_id, group_id),
            )

    async def update_active(self, bot_id: int, active: int) -> None:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "UPDATE botStatus SET bot_active=? WHERE bot=?",
                (active, bot_id),
            )

    async def list_all_bots(self) -> List[int]:
        async with self._db.transaction() as cursor:
            await cursor.execute("SELECT DISTINCT bot FROM botStatus")
            rows = await cursor.fetchall()
            return [r[0] for r in rows] if rows else []