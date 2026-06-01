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
                "SELECT uid, nickname FROM subTarget WHERE uid=?", (uid,)
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return SubTarget(uid=row[0], nickname=row[1])

    async def save(self, uid: str, nickname: str) -> None:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "INSERT INTO subTarget (uid, nickname) VALUES (?, ?)",
                (uid, nickname),
            )

    async def update(self, nickname: str, uid: str) -> None:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "UPDATE subTarget SET nickname=? WHERE uid=?",
                (nickname, uid),
            )
