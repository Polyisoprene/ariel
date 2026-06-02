import time
import httpx
import urllib.parse
from hashlib import md5
from functools import reduce
from typing import Optional, List
from nonebot import logger
from dynamicadaptor.DynamicConversion import formate_message
from arielbot.domain.interfaces.api import BiliContentAPI
from arielbot.infrastructure.adapters.bili_auth import CookieManager

_mixinKeyEncTab = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52
]
_sign_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
    "Referer": "https://www.bilibili.com/"
}

_BASE_HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
    "origin": "https://t.bilibili.com",
}

_WBI_TTL = 3600


class BiliContentAdapter(BiliContentAPI):
    def __init__(self, cookie_manager: CookieManager):
        self._cookie_mgr = cookie_manager
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
        self._img_key: Optional[str] = None
        self._sub_key: Optional[str] = None
        self._wbi_cached_at: float = 0.0

    async def close(self) -> None:
        await self._client.aclose()

    async def _ensure_cookie(self) -> bool:
        cookie = await self._cookie_mgr.ensure_cookie()
        return cookie is not None

    @property
    def _cookie(self) -> Optional[dict]:
        return self._cookie_mgr.cookie

    async def _get_wbi_keys(self) -> None:
        if self._img_key and self._sub_key and time.time() - self._wbi_cached_at < _WBI_TTL:
            return
        try:
            resp = await self._client.get(
                "https://api.bilibili.com/x/web-interface/nav", headers=_sign_headers
            )
            resp.raise_for_status()
            json_content = resp.json()
            img_url = json_content["data"]["wbi_img"]["img_url"]
            sub_url = json_content["data"]["wbi_img"]["sub_url"]
            self._img_key = img_url.rsplit("/", 1)[1].split(".")[0]
            self._sub_key = sub_url.rsplit("/", 1)[1].split(".")[0]
            self._wbi_cached_at = time.time()
        except Exception as e:
            logger.warning(f"获取 WBI keys 失败，将在下次请求时重试: {e}")

    def _get_mixin_key(self, orig: str) -> str:
        return reduce(lambda s, i: s + orig[i], _mixinKeyEncTab, "")[:32]

    async def _enc_wbi(self, params: dict) -> dict:
        if not self._img_key or not self._sub_key:
            raise RuntimeError("WBI keys not initialized")
        mixin_key = self._get_mixin_key(self._img_key + self._sub_key)
        curr_time = round(time.time())
        params["wts"] = curr_time
        params = dict(sorted(params.items()))
        params = {
            k: "".join(filter(lambda chr: chr not in "!'()*", str(v)))
            for k, v in params.items()
        }
        query = urllib.parse.urlencode(params)
        wbi_sign = md5((query + mixin_key).encode()).hexdigest()
        params["w_rid"] = wbi_sign
        return params

    async def get_follow_dynamics(self) -> Optional[list]:
        if not await self._ensure_cookie():
            return None
        headers = {**_BASE_HEADERS, "referer": "https://t.bilibili.com/?spm_id_from=333.1007.0.0"}
        params = {
            "timezone_offset": "-480",
            "type": "all",
            "web_location": "333.1365",
            "platform": "web",
            "page": 1,
            "features": "itemOpusStyle,listOnlyfans,opusBigCover,onlyfansVote,decorationCard,onlyfansAssetsV2,forwardListHidden,ugcDelete,onlyfansQaCard,commentsNewVersion",
        }
        try:
            response = await self._client.get(
                "https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/all",
                headers=headers, cookies=self._cookie, params=params,
            )
            response.raise_for_status()
            data = response.json()
            if data["code"] != 0:
                logger.warning("get dynamic from follow list data code is not 0")
                return None
            return [await formate_message("web", i) for i in data["data"]["items"]]
        except Exception as e:
            logger.warning(f"get dynamic from follow list error {e}")
            return None

    async def get_dynamic_by_id(self, dyn_id: str) -> Optional[object]:
        if not await self._ensure_cookie():
            return None
        await self._get_wbi_keys()
        if self._img_key is None or self._sub_key is None:
            logger.warning("get img_key or sub_key error")
            return None
        headers = {**_BASE_HEADERS, "referer": f"https://t.bilibili.com/{dyn_id}?spm_id_from=333.1365.list.card_time.click"}
        params = {
            "timezone_offset": "-480",
            "platform": "web",
            "gaia_source": "main_web",
            "id": dyn_id,
            "features": "itemOpusStyle,opusBigCover,onlyfansVote,endFooterHidden,decorationCard,onlyfansAssetsV2,ugcDelete,onlyfansQaCard,editable,opusPrivateVisible",
        }
        signed_params = await self._enc_wbi(params)
        try:
            response = await self._client.get(
                "https://api.bilibili.com/x/polymer/web-dynamic/v1/detail",
                headers=headers, params=signed_params, cookies=self._cookie,
            )
            response.raise_for_status()
            return await formate_message("web", response.json()["data"]["item"])
        except Exception as e:
            logger.error(e)
            return None

    async def get_room_info_by_uids(self, uids: List[str]) -> Optional[dict]:
        url = "https://api.live.bilibili.com/room/v1/Room/get_status_info_by_uids"
        try:
            response = await self._client.post(url, headers=_BASE_HEADERS, json={"uids": uids})
            response.raise_for_status()
            return response.json()["data"]
        except Exception as e:
            logger.error(e)
            return None

    async def get_user_info(self, uid: str) -> Optional[dict | str]:
        if not await self._ensure_cookie():
            return "未登录"
        headers = {**_BASE_HEADERS, "Host": "api.bilibili.com", "referer": "https://t.bilibili.com/"}
        params = {"mid": uid, "photo": "true", "web_location": "0.0"}
        try:
            response = await self._client.get(
                "https://api.bilibili.com/x/web-interface/card",
                headers=headers, cookies=self._cookie, params=params,
            )
            response.raise_for_status()
            data = response.json()
            if data["code"] != 0:
                return "未找到相关UP信息"
            return data["data"]
        except Exception as e:
            return str(e)

    async def follow_user(self, uid: str, act: int) -> Optional[bool]:
        if not await self._ensure_cookie():
            return None
        cookie = self._cookie
        if cookie is None:
            return None
        url = 'https://api.bilibili.com/x/relation/modify?statistics={"appId":100,"platform":5}&x-bili-device-req-json={"platform":"web","device":"pc","spmid":"0.0"}'
        data = {
            "fid": str(uid),
            "act": str(act),
            "re_src": "11",
            "gaia_source": "web_main",
            "spmid": "0.0",
            "extend_content": '{"entity":"user","entity_id":477332594}',
            "is_from_frontend_component": "true",
            "csrf": cookie.get("bili_jct", ""),
        }
        try:
            response = await self._client.post(url, headers=_BASE_HEADERS, cookies=cookie, data=data)
            response.raise_for_status()
            resp_data = response.json()
            if resp_data["code"] == 0:
                return True
            return None
        except Exception as e:
            logger.error(e)
            return None