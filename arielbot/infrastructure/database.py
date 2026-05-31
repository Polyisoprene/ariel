import aiosqlite
import asyncio
from os import path, getcwd
from contextlib import asynccontextmanager
from typing import AsyncIterator

_BUSY_RETRIES = 5
_BUSY_DELAY = 0.1


class DatabaseManager:
    def __init__(self, db_path: str = None):
        self._db_path = db_path or path.join(getcwd(), "data.sqlite")

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[aiosqlite.Cursor]:
        conn = await aiosqlite.connect(self._db_path)
        cursor = await conn.cursor()
        await cursor.execute("PRAGMA journal_mode = WAL")
        await cursor.execute("PRAGMA busy_timeout = 5000")
        await cursor.execute("PRAGMA foreign_keys = ON;")
        await cursor.execute("BEGIN")
        try:
            if not path.exists(self._db_path):
                await self._create_tables(cursor)
            yield cursor
            await conn.commit()
        except aiosqlite.Error as e:
            await conn.rollback()
            if "database is locked" in str(e).lower():
                for attempt in range(_BUSY_RETRIES):
                    await asyncio.sleep(_BUSY_DELAY * (attempt + 1))
                    try:
                        await cursor.execute("BEGIN")
                        if not path.exists(self._db_path):
                            await self._create_tables(cursor)
                        yield cursor
                        await conn.commit()
                        return
                    except aiosqlite.Error:
                        continue
            raise
        except Exception:
            await conn.rollback()
            raise
        finally:
            await cursor.close()
            await conn.close()

    async def _create_tables(self, cursor):
        await cursor.executescript("""
            CREATE TABLE IF NOT EXISTS subTarget (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname TEXT NOT NULL,
                uid TEXT NOT NULL UNIQUE,
                live_status INTEGER NOT NULL DEFAULT 1 CHECK(live_status IN (0, 1))
            );
            CREATE TABLE IF NOT EXISTS subChennal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT NOT NULL,
                groupId INTEGER NOT NULL,
                bot INTEGER NOT NULL,
                live_active INTEGER NOT NULL DEFAULT 1 CHECK(live_active IN (0, 1)),
                dyn_active INTEGER NOT NULL DEFAULT 1 CHECK(dyn_active IN (0, 1)),
                FOREIGN KEY (uid) REFERENCES subTarget(uid) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS botStatus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot INTEGER NOT NULL,
                groupId INTEGER NOT NULL,
                push_active INTEGER NOT NULL DEFAULT 1 CHECK(push_active IN (0, 1)),
                bot_active INTEGER NOT NULL DEFAULT 1 CHECK(bot_active IN (0, 1))
            );
            CREATE TABLE IF NOT EXISTS Cookie (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cookie BLOB NOT NULL,
                refresh_token TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS Dynamic (
                dyn_id TEXT NOT NULL PRIMARY KEY,
                uname TEXT NOT NULL,
                dyn_content BLOB NOT NULL
            );
        """)