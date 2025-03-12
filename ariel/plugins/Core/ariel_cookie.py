from ariel_database import DataManager
from nonebot import logger
import pickle
import time

class CookieManager:
    def __init__(self):
        self.cookie = None
        self.refresh_token = None

    async def get_cookie(self):
        async with DataManager() as m:
            result  = await m.select_cookie()
        if result is None:
            logger.info("未登录")
            return            
        self.refresh_token = result[1]
        self.cookie = pickle.loads(result[0])
        await self.check_expire()
    
    async def check_expire(self):
        if self.cookie is None:
            return
        cookie_expire = self.cookie["Expires"]
        now = int(time.time())
        if cookie_expire - now > 3600:
            return
        
    async def refresh_cookie(self):
        pass



    