from typing import Optional
from arielbot.domain.interfaces.repository import CookieRepository
from arielbot.infrastructure.database import DatabaseManager


class SqlCookieRepository(CookieRepository):
    def __init__(self, db: DatabaseManager):
        self._db = db

    async def get(self) -> Optional[tuple]:
        async with self._db.transaction() as cursor:
            await cursor.execute("SELECT cookie, refresh_token FROM Cookie ORDER BY id DESC LIMIT 1")
            return await cursor.fetchone()

    async def save(self, cookie_blob: bytes, refresh_token: str) -> None:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "INSERT INTO Cookie (cookie, refresh_token) VALUES (?, ?)",
                (cookie_blob, refresh_token),
            )

    async def update(self, cookie_blob: bytes, refresh_token: str,
                     old_refresh_token: str) -> None:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "UPDATE Cookie SET cookie=?, refresh_token=? WHERE refresh_token=?",
                (cookie_blob, refresh_token, old_refresh_token),
            )

    async def clear(self) -> None:
        async with self._db.transaction() as cursor:
            await cursor.execute("DELETE FROM Cookie")