import httpx
from nonebot import logger

class Login:
    def __init__(self):
        self.qrcode_key = None
        self.headers  = {
        "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
        }
    

    async def get_qrcode_key(self):
        url = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
        try:
            response = httpx.get(url,headers=self.headers)
            if response.status_code==200:
                self.qrcode_key = response.json()["qrcode_key"]
                return response.json()["url"]
        except Exception as e:
            logger.error(e)
            return None

