import asyncio
import qrcode
from io import BytesIO
from arielbot.domain.interfaces.api import BiliAuthAPI
from arielbot.domain.interfaces.repository import CookieRepository
from nonebot.adapters.onebot.v11 import MessageSegment


class AuthService:
    def __init__(self, auth_api: BiliAuthAPI, cookie_repo: CookieRepository,
                 bot_client, parse_cookie_fn, serialize_cookie_fn,
                 cookie_manager=None):
        self._auth_api = auth_api
        self._cookie_repo = cookie_repo
        self._bot_client = bot_client
        self._parse_cookie = parse_cookie_fn
        self._serialize_cookie = serialize_cookie_fn
        self._cookie_manager = cookie_manager

    async def login(self, bot, event):
        scan_url = await self._auth_api.get_qrcode()
        if scan_url is None:
            await bot.send(event=event, message=MessageSegment.text("获取扫码链接失败"))
            return

        qrcode_buffer = BytesIO()
        qr = qrcode.QRCode()
        qr.add_data(scan_url)
        img = qr.make_image(image_factory=qrcode.image.pure.PyPNGImage)
        img.save(qrcode_buffer)
        await bot.send(event, message=MessageSegment.image(qrcode_buffer))

        deadline = asyncio.get_event_loop().time() + 300
        while True:
            if asyncio.get_event_loop().time() > deadline:
                await bot.send(event, "登录超时，请重新尝试")
                break
            scan_result = await self._auth_api.poll_scan()
            if scan_result is None or scan_result.get("code") == 86038:
                await bot.send(event, "登陆失败")
                break
            if scan_result.get("code") == 0:
                cookies = self._parse_cookie(scan_result)
                refresh_token = scan_result.get("refresh_token")
                if cookies is None or refresh_token is None:
                    await bot.send(event, MessageSegment.text("cookie 解析失败"))
                    break
                await self._cookie_repo.clear()
                await self._cookie_repo.save(
                    self._serialize_cookie(cookies), refresh_token
                )
                if self._cookie_manager:
                    await self._cookie_manager.load_cookie()
                break
            await asyncio.sleep(3)