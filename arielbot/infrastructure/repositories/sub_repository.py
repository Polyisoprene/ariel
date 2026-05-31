from typing import List, Optional, Tuple
from arielbot.domain.interfaces.repository import SubChannelRepository
from arielbot.domain.entities import SubChannel
from arielbot.infrastructure.database import DatabaseManager


class SqlSubChannelRepository(SubChannelRepository):
    def __init__(self, db: DatabaseManager):
        self._db = db

    async def get(self, uid: str, group_id: int, bot_id: int) -> Optional[SubChannel]:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "SELECT uid, groupId, bot, live_active, dyn_active FROM subChennal WHERE uid=? AND groupId=? AND bot=?",
                (uid, group_id, bot_id),
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return SubChannel(
                uid=row[0], group_id=row[1], bot_id=row[2],
                live_active=bool(row[3]), dyn_active=bool(row[4]),
            )

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