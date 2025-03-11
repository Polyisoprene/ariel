import aiosqlite
from os import path,getcwd
from typing import Optional

class DataManager:
    def __init__(self):
        self.conn: Optional[aiosqlite.Connection] = None
        self.cursor:Optional[aiosqlite.Cursor] = None

    async def __aenter__(self):
        db_path = path.join(getcwd(),"data.sqlit")
        self.conn = await aiosqlite.connect(db_path)
        self.cursor = await self.conn.cursor()
        await self._cursor.execute("BEGIN")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.conn.commit()
        else:
            await self.conn.rollback()
        await self._cursor.close()
        await self.conn.close()
        self._cursor = None
        self.conn = None
        return False
    

    async def creat_user_table(self):
        pass
        
    