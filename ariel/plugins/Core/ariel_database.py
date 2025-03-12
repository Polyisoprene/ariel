import aiosqlite
from os import path,getcwd
from typing import Optional

class DataManager:
    def __init__(self):
        self.__conn: Optional[aiosqlite.Connection] = None
        self.__cursor:Optional[aiosqlite.Cursor] = None
        self.dbexists = True

    async def __aenter__(self):
        db_path = path.join(getcwd(),"data.sqlit")
        if not path.exists(db_path):
            self.dbexists=False
        self.__conn = await aiosqlite.connect(db_path)
        self.__cursor = await self.__conn.cursor()
        await self.__cursor.execute("BEGIN")
        if not self.dbexists:
            await self.__cursor.execute("PRAGMA foreign_keys = ON;")
            await self.__creat_subTarget_table()
            await self.__creat_subChennal_table()
            await self.__creat_botStatus_table()
            await self.__creat_cookie_table()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.__conn.commit()
        else:
            await self.__conn.rollback()
        await self.__cursor.close()
        await self.__conn.close()
        self.__cursor = None
        self.__conn = None
    
    async def __creat_subTarget_table(self):
        sql ="""
            CREATE TABLE IF NOT EXISTS subTarget (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                nickname TEXT NOT NULL,
                uid TEXT NOT NULL,
                live_status INTEGER NOT NULL DEFAULT 1 CHECK(live_status IN (0, 1))
            );
            """
        
        await self.__cursor.execute(sql)
    
    async def __creat_subChennal_table(self):
        sql ="""
            CREATE TABLE IF NOT EXISTS subChennal (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                uid TEXT NOT NULL,
                groupId INTEGER NOT NULL,
                bot INTEGER NOT NULL,
                live_active INTEGER NOT NULL DEFAULT 1 CHECK(live_active IN (0, 1)),
                dyn_active INTEGER NOT NULL DEFAULT 1 CHECK(dyn_active IN (0, 1)),
                FOREIGN KEY (uid) 
                REFERENCES subTarget(uid) 
                ON DELETE CASCADE
            );
            """
        await self.__cursor.execute(sql)
        
    async def __creat_botStatus_table(self):
        sql ="""
            CREATE TABLE IF NOT EXISTS botStatus (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                bot INTEGER NOT NULL,
                groupId INTEGER NOT NULL,
                push_active INTEGER NOT NULL DEFAULT 1 CHECK(push_active IN (0, 1)),
                bot_active INTEGER NOT NULL DEFAULT 1 CHECK(bot_active IN (0, 1))
            );
            """
        await self.__cursor.execute(sql)
            
    async def __creat_cookie_table(self):
        sql ="""
            CREATE TABLE IF NOT EXISTS Cookie (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                cookie  BLOB NOT NULL,
                refresh_token  TEXT NOT NULL
            );
            """
        await self.__cursor.execute(sql)

# cookie process
    async def select_cookie(self):
        sql = "SELECT cookie, refresh_token FROM Cookie"
        await self.__cursor.execute(sql)
        return await self.__cursor.fetchone()  
    
    async def insert_cookie(self,data:set):
        sql = "INSERT INTO Cookie (cookie,refresh_token) VALUES (?, ?);"
        await self.__cursor.execute(sql,data)
