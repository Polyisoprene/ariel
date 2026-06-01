from typing import Optional
from arielbot.domain.interfaces.repository import DynCacheRepository
from arielbot.infrastructure.database import DatabaseManager


class SqlDynCacheRepository(DynCacheRepository):
    def __init__(self, db: DatabaseManager):
        self._db = db

    async def exists(self, dyn_id: str) -> bool:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "SELECT 1 FROM Dynamic WHERE dyn_id=?",
                (dyn_id,),
            )
            return (await cursor.fetchone()) is not None

    async def save(self, dyn_id: str, uname: str, content: bytes) -> None:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "INSERT OR IGNORE INTO Dynamic (dyn_id, uname, dyn_content) "
                "VALUES (?, ?, ?)",
                (dyn_id, uname, content),
            )

    async def find(self, dyn_id: str) -> Optional[bytes]:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "SELECT dyn_content FROM Dynamic WHERE dyn_id=?",
                (dyn_id,),
            )
            row = await cursor.fetchone()
            if row:
                return row[0]
            await cursor.execute(
                "SELECT dyn_content FROM DynamicArchive WHERE dyn_id=?",
                (dyn_id,),
            )
            row = await cursor.fetchone()
            return row[0] if row else None

    async def archive_old_dynamics(self, days: int = 7) -> None:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "INSERT OR IGNORE INTO DynamicArchive (dyn_id, uname, dyn_content) "
                "SELECT dyn_id, uname, dyn_content FROM Dynamic "
                "WHERE created_at < datetime('now', ?)",
                (f"-{days} days",),
            )
            await cursor.execute(
                "DELETE FROM Dynamic WHERE created_at < datetime('now', ?)",
                (f"-{days} days",),
            )
