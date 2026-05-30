from typing import Optional
from arielbot.domain.interfaces.repository import DynCacheRepository
from arielbot.infrastructure.database import DatabaseManager


class SqlDynCacheRepository(DynCacheRepository):
    def __init__(self, db: DatabaseManager):
        self._db = db

    async def exists(self, dyn_id: str) -> Optional[bytes]:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "SELECT dyn_content FROM Dynamic WHERE dyn_id=?",
                (dyn_id,),
            )
            row = await cursor.fetchone()
            return row[0] if row else None

    async def save(self, dyn_id: str, uname: str, content: bytes) -> None:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "INSERT INTO Dynamic (dyn_id, uname, dyn_content) VALUES (?, ?, ?)",
                (dyn_id, uname, content),
            )

    async def get_content(self, dyn_id: str) -> Optional[bytes]:
        return await self.exists(dyn_id)