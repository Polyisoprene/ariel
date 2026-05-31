import re
import time
import httpx
import pickle
import binascii
from typing import Optional
from nonebot import logger
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from http.cookies import SimpleCookie
from datetime import datetime, timezone
from arielbot.domain.interfaces.api import BiliAuthAPI

_RSA_KEY = RSA.importKey(
    "-----BEGIN PUBLIC KEY-----\n"
    "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDLgd2OAkcGVtoE3ThUREbio0Eg\n"
    "Uc/prcajMKXvkCKFCWhJYJcLkcM2DKKcSeFpD/j6Boy538YXnR6VhcuUJOhH2x71\n"
    "nzPjfdTcqMz7djHum0qSZA0AyCBDABUqCrfNgCiJ00Ra7GmRj+YCK1NJEuewlb40\n"
    "JNrRuoEUXpabUzGB8QIDAQAB\n"
    "-----END PUBLIC KEY-----"
)
_HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
}


class BiliAuthAdapter(BiliAuthAPI):
    def __init__(self):
        self.qrcode_key = None
        self.headers = _HEADERS.copy()

    async def get_qrcode(self) -> Optional[str]:
        url = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                self.qrcode_key = data["data"]["qrcode_key"]
                return data["data"]["url"]
        except Exception as e:
            logger.error(e)
            return None

    async def poll_scan(self) -> Optional[dict]:
        url = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
        params = {"qrcode_key": self.qrcode_key}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                return response.json()["data"]
        except Exception as e:
            logger.error(e)
            return None


class CookieManager:
    def __init__(self, cookie_repo):
        self._cookie_repo = cookie_repo
        self._cookie = None
        self._refresh_token = None
        self.headers = _HEADERS.copy()

    @property
    def cookie(self):
        return self._cookie

    @property
    def refresh_token(self):
        return self._refresh_token

    async def ensure_cookie(self) -> Optional[dict]:
        if self._cookie is None:
            await self.load_cookie()
        return self._cookie

    async def load_cookie(self):
        result = await self._cookie_repo.get()
        if result is None:
            logger.info("未登录")
            return
        self._refresh_token = result[1]
        self._cookie = pickle.loads(result[0])
        await self._check_expire()

    async def _check_expire(self):
        if self._cookie is None:
            return
        cookie_expire = self._cookie.get("Expires")
        if cookie_expire is None:
            await self._refresh_cookie()
            return
        now = int(time.time())
        if int(cookie_expire) - now > 3600:
            return
        await self._refresh_cookie()

    async def _refresh_cookie(self):
        correspond_path = await self._get_correspond_path()
        if correspond_path is None:
            return
        refresh_csrf = await self._get_refresh_csrf(correspond_path)
        if refresh_csrf is None:
            return
        new_data = await self._get_new_cookie(refresh_csrf)
        if new_data is None:
            return
        self._cookie = new_data[0]
        new_token = new_data[1]
        await self._cookie_repo.update(
            pickle.dumps(self._cookie), new_token, self._refresh_token
        )
        self._refresh_token = new_token

    async def _get_correspond_path(self):
        params = {"csrf": self._cookie.get("bili_jct", "")}
        url = "https://passport.bilibili.com/x/passport-login/web/cookie/info"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params, cookies=self._cookie)
                cipher = PKCS1_OAEP.new(_RSA_KEY, SHA256)
                encrypted = cipher.encrypt(
                    f"refresh_{response.json()['data']['timestamp']}".encode()
                )
                return binascii.b2a_hex(encrypted).decode()
        except Exception as e:
            logger.error(e)
            return None

    async def _get_refresh_csrf(self, correspond_path):
        url = f"https://www.bilibili.com/correspond/1/{correspond_path}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, cookies=self._cookie)
                pattern = re.compile(
                    r'<div\s+id\s*=\s*["\']1-name["\']\s*>(.*?)</div>', flags=re.DOTALL
                )
                match = pattern.search(response.text)
                if not match:
                    return None
                return match.group(1).strip()
        except Exception as e:
            logger.error("get refresh_csrf error")
            logger.error(e)
            return None

    async def _get_new_cookie(self, refresh_csrf):
        url = "https://passport.bilibili.com/x/passport-login/web/cookie/refresh"
        data = {
            "csrf": self._cookie.get("bili_jct", ""),
            "refresh_csrf": refresh_csrf,
            "source": "main_web",
            "refresh_token": self._refresh_token,
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, data=data, cookies=self._cookie)
                new_refresh_token = response.json()["data"]["refresh_token"]
                new_cookies = [v for k, v in response.headers.multi_items() if k.lower() == "set-cookie"]
                parsed_cookies = [self._parse_cookie_attributes(c) for c in new_cookies]
                if not parsed_cookies:
                    return None
                expires = parsed_cookies[0]["expires"]
                dt = datetime.strptime(expires, "%a, %d %b %Y %H:%M:%S GMT").replace(
                    tzinfo=timezone.utc
                )
                new_cookie = {}
                timestamp = int(dt.timestamp())
                for item in parsed_cookies:
                    new_cookie[item["name"]] = item["value"]
                new_cookie["Expires"] = str(timestamp)
                return (new_cookie, new_refresh_token)
        except Exception as e:
            logger.error("get new cookie error")
            logger.error(e)
            return None

    def _parse_cookie_attributes(self, cookie_str: str) -> dict:
        cookie = SimpleCookie()
        cookie.load(cookie_str)
        for key, morsel in cookie.items():
            return {
                "name": key,
                "value": morsel.value,
                "expires": morsel.get("expires", None),
            }
        return {}