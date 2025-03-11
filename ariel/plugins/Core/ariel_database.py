import aiosqlite
from os import path,getcwd
from typing import Optional

class DataManager:
    def __init__(self):
        self._conn: Optional[aiosqlite.Connection] = None
        self._cursor:Optional[aiosqlite.Cursor] = None
        self.dbexists = True

    async def __aenter__(self):
        db_path = path.join(getcwd(),"data.sqlit")
        if not path.exists(db_path):
            self.dbexists=False
        self._conn = await aiosqlite.connect(db_path)
        self._cursor = await self.conn.cursor()
        await self._cursor.execute("BEGIN")
        if not self.dbexists:
            await self._cursor.execute("PRAGMA foreign_keys = ON;")
            await self._creat_subTarget_table()
            await self._creat_subChennal_table()
            await self._creat_botStatus_table()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self._conn.commit()
        else:
            await self._conn.rollback()
        await self._cursor.close()
        await self._conn.close()
        self._cursor = None
        self._conn = None
        return False
    
    async def _creat_subTarget_table(self):
        sql ="""
            CREATE TABLE IF NOT EXISTS subTarget (
                index INTEGER PRIMARY KEY AUTOINCREMENT, 
                nickname TEXT NOT NULL,
                uid TEXT NOT NULL,
                live_status INTEGER NOT NULL DEFAULT 1 CHECK(live_active IN (0, 1)),
            );
            """
        
        await self.cursor.execute(sql)
    
    async def _creat_subChennal_table(self):
        sql ="""
            CREATE TABLE IF NOT EXISTS subChennal (
                index INTEGER PRIMARY KEY AUTOINCREMENT, 
                uid TEXT NOT NULL,
                group INTEGER NOT NULL,
                bot INTEGER NOT NULL,
                live_active INTEGER NOT NULL DEFAULT 1 CHECK(live_active IN (0, 1)),
                dyn_active INTEGER NOT NULL DEFAULT 1 CHECK(live_active IN (0, 1)),
                FOREIGN KEY (uid) 
                REFERENCES subTarget(uid) 
                ON DELETE CASCADE
            );
            """
        await self.cursor.execute(sql)
        
    async def _creat_botStatus_table(self):
        sql ="""
            CREATE TABLE IF NOT EXISTS subChennal (
                index INTEGER PRIMARY KEY AUTOINCREMENT, 
                bot INTEGER NOT NULL,
                group INTEGER NOT NULL,
                push_active INTEGER NOT NULL DEFAULT 1 CHECK(live_active IN (0, 1)),
                bot_active INTEGER NOT NULL DEFAULT 1 CHECK(live_active IN (0, 1)),
                FOREIGN KEY (uid) 
                REFERENCES subTarget(uid) 
                ON DELETE CASCADE
            );
            """
        await self._cursor.execute(sql)
            
    async def _creat_cookie_table(self):
        sql ="""
            CREATE TABLE IF NOT EXISTS subChennal (
                index INTEGER PRIMARY KEY AUTOINCREMENT, 
                bot INTEGER NOT NULL,
                group INTEGER NOT NULL,
                push_active INTEGER NOT NULL DEFAULT 1 CHECK(live_active IN (0, 1)),
                bot_active INTEGER NOT NULL DEFAULT 1 CHECK(live_active IN (0, 1)),
                FOREIGN KEY (uid) 
                REFERENCES subTarget(uid) 
                ON DELETE CASCADE
            );
            """
        await self._cursor.execute(sql)

    