from typing import List, Optional
from arielbot.domain.interfaces.repository import SubTargetRepository
from arielbot.domain.entities import SubTarget
from arielbot.infrastructure.database import DatabaseManager


class SqlSubTargetRepository(SubTargetRepository):
    def __init__(self, db: DatabaseManager):
        self._db = db

    async def get(self, uid: str) -> Optional[SubTarget]:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "SELECT uid, nickname, live_status FROM subTarget WHERE uid=?", (uid,)
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return SubTarget(uid=row[0], nickname=row[1], live_status=row[2])

    async def save(self, uid: str, nickname: str, live_status: int) -> None:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "INSERT INTO subTarget (uid, nickname, live_status) VALUES (?, ?, ?)",
                (uid, nickname, live_status),
            )

    async def update(self, nickname: str, live_status: int, uid: str) -> None:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "UPDATE subTarget SET nickname=?, live_status=? WHERE uid=?",
                (nickname, live_status, uid),
            )
