from typing import List, Optional, Tuple
from arielbot.domain.interfaces.repository import SubTargetRepository, SubChannelRepository
from arielbot.infrastructure.database import DatabaseManager


class SqlSubTargetRepository(SubTargetRepository):
    def __init__(self, db: DatabaseManager):
        self._db = db

    async def get(self, uid: str) -> Optional[tuple]:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "SELECT nickname FROM subTarget WHERE uid=?", (uid,)
            )
            return await cursor.fetchone()

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


class SqlSubChannelRepository(SubChannelRepository):
    def __init__(self, db: DatabaseManager):
        self._db = db

    async def get(self, uid: str, group_id: int, bot_id: int) -> Optional[tuple]:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "SELECT live_active, dyn_active FROM subChennal WHERE uid=? AND groupId=? AND bot=?",
                (uid, group_id, bot_id),
            )
            return await cursor.fetchone()

    async def save(self, uid: str, group_id: int, bot_id: int) -> None:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "INSERT INTO subChennal (uid, groupId, bot) VALUES (?, ?, ?)",
                (uid, group_id, bot_id),
            )

    async def update(self, live_active: int, dyn_active: int,
                     uid: str, group_id: int, bot_id: int) -> None:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "UPDATE subChennal SET live_active=?, dyn_active=? WHERE uid=? AND groupId=? AND bot=?",
                (live_active, dyn_active, uid, group_id, bot_id),
            )

    async def find_push_targets_for_dyn(self, uid: str) -> List[Tuple[int, int]]:
        async with self._db.transaction() as cursor:
            await cursor.execute("""
                SELECT DISTINCT t2.groupId, t2.bot
                FROM subTarget t1
                INNER JOIN subChennal t2 ON t1.uid = t2.uid
                INNER JOIN botStatus t3 ON t2.groupId = t3.groupId AND t2.bot = t3.bot
                WHERE t1.uid = ?
                  AND t3.push_active = 1
                  AND t2.dyn_active = 1
                  AND t3.bot_active = 1
            """, (uid,))
            rows = await cursor.fetchall()
            return [(r[0], r[1]) for r in rows] if rows else []

    async def find_push_targets_for_live(self, uid: str) -> List[Tuple[int, int]]:
        async with self._db.transaction() as cursor:
            await cursor.execute("""
                SELECT DISTINCT t2.groupId, t2.bot
                FROM subTarget t1
                INNER JOIN subChennal t2 ON t1.uid = t2.uid
                INNER JOIN botStatus t3 ON t2.groupId = t3.groupId AND t2.bot = t3.bot
                WHERE t1.uid = ?
                  AND t3.push_active = 1
                  AND t2.live_active = 1
                  AND t3.bot_active = 1
            """, (uid,))
            rows = await cursor.fetchall()
            return [(r[0], r[1]) for r in rows] if rows else []

    async def find_live_check_uids(self) -> List[tuple]:
        async with self._db.transaction() as cursor:
            await cursor.execute("""
                SELECT DISTINCT t1.uid, t1.live_status
                FROM subTarget t1
                INNER JOIN subChennal t2 ON t1.uid = t2.uid
                INNER JOIN botStatus t3 ON t2.groupId = t3.groupId AND t2.bot = t3.bot
                WHERE t3.push_active = 1
                  AND t2.live_active = 1
                  AND t3.bot_active = 1
            """)
            return await cursor.fetchall()

    async def list_by_group(self, bot_id: int, group_id: int) -> List[tuple]:
        async with self._db.transaction() as cursor:
            await cursor.execute("""
                SELECT DISTINCT t1.uid, t1.nickname, t2.live_active, t2.dyn_active
                FROM subTarget t1
                INNER JOIN subChennal t2 ON t1.uid = t2.uid
                WHERE t2.bot = ? AND t2.groupId = ?
            """, (bot_id, group_id))
            return await cursor.fetchall()