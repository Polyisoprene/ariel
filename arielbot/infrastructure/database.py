import aiosqlite
from os import path, getcwd
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional
from nonebot import logger


class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        self._db_path: str = db_path or path.join(getcwd(), "data.sqlite")
        self._initialized: bool = False

    async def _ensure_initialized(self, conn: aiosqlite.Connection) -> None:
        if self._initialized:
            return
        cursor = await conn.cursor()
        try:
            await self._create_tables(cursor)
            await self._migrate(cursor)
            await self._create_indexes(cursor)
            await conn.commit()
        finally:
            await cursor.close()
        self._initialized = True

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[aiosqlite.Cursor]:
        conn = await aiosqlite.connect(self._db_path)
        cursor = await conn.cursor()
        await cursor.execute("PRAGMA journal_mode = WAL")
        await cursor.execute("PRAGMA busy_timeout = 5000")
        await cursor.execute("PRAGMA foreign_keys = ON;")
        await self._ensure_initialized(conn)
        await cursor.execute("BEGIN")
        try:
            yield cursor
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise
        finally:
            await cursor.close()
            await conn.close()

    async def _create_tables(self, cursor: aiosqlite.Cursor) -> None:
        await cursor.executescript("""
            CREATE TABLE IF NOT EXISTS subTarget (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname TEXT NOT NULL,
                uid TEXT NOT NULL UNIQUE,
                live_status INTEGER NOT NULL DEFAULT 1 CHECK(live_status IN (0, 1))
            );
            CREATE TABLE IF NOT EXISTS subChannel (
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
                bot_active INTEGER NOT NULL DEFAULT 1 CHECK(bot_active IN (0, 1)),
                UNIQUE(bot, groupId)
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
            CREATE TABLE IF NOT EXISTS DynamicArchive (
                dyn_id TEXT NOT NULL PRIMARY KEY,
                uname TEXT NOT NULL,
                dyn_content BLOB NOT NULL,
                archived_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)

    async def _migrate(self, cursor: aiosqlite.Cursor) -> None:
        try:
            await cursor.execute("PRAGMA table_info(Dynamic)")
            columns = [row[1] for row in await cursor.fetchall()]
            if "created_at" not in columns:
                await cursor.execute(
                    "ALTER TABLE Dynamic ADD COLUMN created_at TIMESTAMP"
                )
                await cursor.execute(
                    "UPDATE Dynamic SET created_at = datetime('now', '+8 hours')"
                )
                logger.info("Migration: added created_at to Dynamic table")
        except Exception as e:
            logger.warning(f"Dynamic migration skipped: {e}")

        try:
            await cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='subChennal'"
            )
            if await cursor.fetchone():
                await cursor.execute("ALTER TABLE subChennal RENAME TO subChannel")
                logger.info("Migration: renamed subChennal → subChannel")
        except Exception as e:
            logger.warning(f"subChennal rename skipped: {e}")

        try:
            await cursor.execute(
                "SELECT 1 FROM subChannel "
                "GROUP BY uid, groupId, bot HAVING COUNT(*) > 1 LIMIT 1"
            )
            has_dupes = await cursor.fetchone()
            if has_dupes:
                await cursor.execute("""
                    DELETE FROM subChannel WHERE id NOT IN (
                        SELECT MAX(id) FROM subChannel GROUP BY uid, groupId, bot
                    )
                """)
                logger.info(
                    f"Migration: removed {cursor.rowcount} duplicate subChannel rows"
                )
        except Exception as e:
            logger.warning(f"subChannel dedup skipped: {e}")

    async def _create_indexes(self, cursor: aiosqlite.Cursor) -> None:
        await cursor.executescript("""
            CREATE INDEX IF NOT EXISTS idx_subchannel_uid ON subChannel(uid);
            CREATE INDEX IF NOT EXISTS idx_subchannel_group_bot
                ON subChannel(groupId, bot);
            CREATE INDEX IF NOT EXISTS idx_botstatus_group_bot
                ON botStatus(groupId, bot);
        """)
        try:
            await cursor.executescript("""
                CREATE UNIQUE INDEX IF NOT EXISTS uidx_subchannel_uid_group_bot
                    ON subChannel(uid, groupId, bot);
            """)
        except Exception as e:
            logger.warning(f"subChannel unique index skipped: {e}")