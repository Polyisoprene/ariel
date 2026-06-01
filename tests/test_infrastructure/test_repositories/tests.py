import pytest
import aiosqlite
import asyncio
from unittest.mock import AsyncMock, MagicMock
from arielbot.infrastructure.database import DatabaseManager


class TestDatabaseManager:
    @pytest.fixture
    def db(self):
        return DatabaseManager(":memory:")

    @pytest.mark.asyncio
    async def test_transaction_creates_tables(self, db):
        async with db.transaction() as cursor:
            await cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in await cursor.fetchall()]
            assert "subTarget" in tables
            assert "subChennal" in tables
            assert "botStatus" in tables
            assert "Cookie" in tables
            assert "Dynamic" in tables

    @pytest.mark.asyncio
    async def test_transaction_commit(self, db):
        async with db.transaction() as cursor:
            await cursor.execute(
                "INSERT INTO subTarget (uid, nickname, live_status) VALUES (?, ?, ?)",
                ("1", "test", 0),
            )
        async with db.transaction() as cursor:
            await cursor.execute("SELECT uid FROM subTarget WHERE uid='1'")
            row = await cursor.fetchone()
            assert row is not None

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, db):
        async with db.transaction() as cursor:
            await cursor.execute(
                "INSERT INTO subTarget (uid, nickname, live_status) VALUES (?, ?, ?)",
                ("1", "test", 0),
            )
        with pytest.raises(RuntimeError):
            async with db.transaction() as cursor:
                await cursor.execute(
                    "INSERT INTO subTarget (uid, nickname, live_status) VALUES (?, ?, ?)",
                    ("1", "dup", 0),
                )
                raise RuntimeError("force rollback")
        async with db.transaction() as cursor:
            await cursor.execute("SELECT nickname FROM subTarget WHERE uid='1'")
            row = await cursor.fetchone()
            assert row[0] == "test"


class TestSubRepositories:
    @pytest.fixture
    async def db(self):
        manager = DatabaseManager(":memory:")
        async with manager.transaction():
            yield manager

    @pytest.mark.asyncio
    async def test_sub_target_repository(self, db):
        from arielbot.infrastructure.repositories.sub_repository import SqlSubTargetRepository
        repo = SqlSubTargetRepository(db)
        await repo.save("1", "name", 0)
        row = await repo.get("1")
        assert row[0] == "name"
        await repo.update("newname", 1, "1")
        row = await repo.get("1")
        assert row[0] == "newname"

    @pytest.mark.asyncio
    async def test_sub_channel_repository_save_get_update(self, db):
        from arielbot.infrastructure.repositories.sub_repository import SqlSubChannelRepository
        repo = SqlSubChannelRepository(db)
        await repo.save("1", 100, 200)
        row = await repo.get("1", 100, 200)
        assert row[0] == 1  # live_active default
        assert row[1] == 1  # dyn_active default
        await repo.update(0, 0, "1", 100, 200)
        row = await repo.get("1", 100, 200)
        assert row[0] == 0

    @pytest.mark.asyncio
    async def test_bot_status_repository(self, db):
        from arielbot.infrastructure.repositories.bot_repository import SqlBotStatusRepository
        repo = SqlBotStatusRepository(db)
        assert await repo.get(1, 2) is None
        await repo.save(1, 2, 1, 1)
        row = await repo.get(1, 2)
        assert row[0] == 1
        await repo.update_push(1, 2, 0)
        row = await repo.get(1, 2)
        assert row[0] == 0
        await repo.update_active(1, 0)
        row = await repo.get(1, 2)
        assert row[1] == 0
        bots = await repo.list_all_bots()
        assert 1 in bots

    @pytest.mark.asyncio
    async def test_cookie_repository(self, db):
        from arielbot.infrastructure.repositories.cookie_repository import SqlCookieRepository
        repo = SqlCookieRepository(db)
        assert await repo.get() is None
        await repo.save(b"data", "token")
        row = await repo.get()
        assert row[0] == b"data"
        await repo.update(b"new", "token2", "token")
        row = await repo.get()
        assert row[0] == b"new"
        await repo.clear()
        assert await repo.get() is None

    @pytest.mark.asyncio
    async def test_dyn_cache_repository(self, db):
        from arielbot.infrastructure.repositories.dyn_repository import SqlDynCacheRepository
        repo = SqlDynCacheRepository(db)
        assert await repo.exists("1") is None
        await repo.save("1", "up", b"content")
        assert await repo.exists("1") == b"content"
        assert await repo.get_content("1") == b"content"