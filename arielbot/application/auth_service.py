import asyncio
import qrcode
from io import BytesIO
from arielbot.domain.interfaces.api import BiliAuthAPI
from arielbot.domain.interfaces.repository import CookieRepository

_POLL_INTERVAL = 3
_LOGIN_TIMEOUT = 300


class AuthService:
    def __init__(self, auth_api: BiliAuthAPI, cookie_repo: CookieRepository,
                 bot_client, parse_cookie_fn, serialize_cookie_fn,
                 cookie_manager=None, build_text=None, build_image=None):
        self._auth_api = auth_api
        self._cookie_repo = cookie_repo
        self._bot_client = bot_client
        self._parse_cookie = parse_cookie_fn
        self._serialize_cookie = serialize_cookie_fn
        self._cookie_manager = cookie_manager
        self._build_text = build_text or (lambda s: s)
        self._build_image = build_image or (lambda b: b)

    async def login(self, bot, event):
        scan_url = await self._auth_api.get_qrcode()
        if scan_url is None:
            await bot.send(event=event, message=self._build_text("获取扫码链接失败"))
            return

        await self._send_qrcode(bot, event, scan_url)

        try:
            scan_result = await asyncio.wait_for(
                self._poll_scan_result(), timeout=_LOGIN_TIMEOUT
            )
        except asyncio.TimeoutError:
            await bot.send(event, "登录超时，请重新尝试")
            return

        if scan_result is None:
            await bot.send(event, "登陆失败")
            return

        await self._save_login_cookie(bot, event, scan_result)

    async def _send_qrcode(self, bot, event, scan_url: str):
        qrcode_buffer = BytesIO()
        qr = qrcode.QRCode()
        qr.add_data(scan_url)
        img = qr.make_image(image_factory=qrcode.image.pure.PyPNGImage)
        img.save(qrcode_buffer)
        await bot.send(event, message=self._build_image(qrcode_buffer))

    async def _poll_scan_result(self):
        while True:
            scan_result = await self._auth_api.poll_scan()
            if scan_result is None or scan_result.get("code") == 86038:
                return None
            if scan_result.get("code") == 0:
                return scan_result
            await asyncio.sleep(_POLL_INTERVAL)

    async def _save_login_cookie(self, bot, event, scan_result: dict):
        cookies = self._parse_cookie(scan_result)
        refresh_token = scan_result.get("refresh_token")
        if cookies is None or refresh_token is None:
            await bot.send(event, self._build_text("cookie 解析失败"))
            return

        await self._cookie_repo.clear()
        await self._cookie_repo.save(
            self._serialize_cookie(cookies), refresh_token
        )
        if self._cookie_manager:
            await self._cookie_manager.load_cookie()
