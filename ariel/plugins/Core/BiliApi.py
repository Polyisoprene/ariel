import httpx
from typing import Optional
from nonebot import logger




class Login:
    def __init__(self):
        self.qrcode_key = None
        self.headers  = {
        "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
        }

    async def check_scan_result(self) -> Optional[dict]:
        """获取登陆二维码扫描结果

        :return: {
                        "code": 0,
                        "message": "0",
                        "ttl": 1,
                        "data": {
                            "url": "https://passport.biligame.com/crossDomain?DedeUserID=&DedeUserID__ckMd5=*&Expires=*&SESSDATA=*&bili_jct=**&gourl=*",
                            "refresh_token": "***",
                            "timestamp": 1662363009601,
                            "code": 0,
                            "message": ""
                        }
                    }
        :rtype: Optional[dict]
        """

        url = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
        params = {
            "qrcode_key":self.qrcode_key
        }
        try:
            response = httpx.get(url,headers=self.headers,params=params)
            if response.status_code != 200:
                return response.json()["data"]
            return None
        except Exception as e:
            logger.error(e)
            return None


    async def get_qrcode_key(self):
        url = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
        try:
            response = httpx.get(url,headers=self.headers)
            if response.status_code !=200:
                return None
            self.qrcode_key = response.json()["data"]["qrcode_key"]
            return response.json()["data"]["url"]
        except Exception as e:
            logger.error(e)
            return None

