import time
import qrcode
from io import BytesIO
from arielbot.domain.interfaces.api import BiliAuthAPI
from arielbot.domain.interfaces.repository import CookieRepository
from nonebot.adapters.onebot.v11 import MessageSegment


class AuthService:
    def __init__(self, auth_api: BiliAuthAPI, cookie_repo: CookieRepository,
                 bot_client, parse_cookie_fn, serialize_cookie_fn):
        self._auth_api = auth_api
        self._cookie_repo = cookie_repo
        self._bot_client = bot_client
        self._parse_cookie = parse_cookie_fn
        self._serialize_cookie = serialize_cookie_fn

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

        while True:
            scan_result = await self._auth_api.poll_scan()
            if scan_result is None or scan_result["code"] == 86038:
                await bot.send(event, "登陆失败")
                break
            if scan_result["code"] == 0:
                cookies = self._parse_cookie(scan_result)
                if cookies is None:
                    await bot.send(event, MessageSegment.text("cookie 解析失败"))
                    break
                await self._cookie_repo.clear()
                await self._cookie_repo.save(
                    self._serialize_cookie(cookies), scan_result["refresh_token"]
                )
                break
            time.sleep(3)