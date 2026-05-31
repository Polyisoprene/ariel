import asyncio
import os
import pickle
import skia
from io import BytesIO
from typing import List, Optional
from arielbot.domain.interfaces.api import BiliContentAPI
from arielbot.domain.interfaces.repository import DynCacheRepository, SubChannelRepository
from arielbot.domain.interfaces.renderer import DynRenderer, SubListRenderer

_HELP_CACHE_PATH = os.path.join(os.getcwd(), "data", "help.png")


class QueryService:
    def __init__(self, content_api: BiliContentAPI,
                 dyn_cache_repo: DynCacheRepository,
                 sub_channel_repo: SubChannelRepository,
                 dyn_renderer: DynRenderer,
                 sub_list_renderer: SubListRenderer):
        self._api = content_api
        self._dyn_cache_repo = dyn_cache_repo
        self._sub_channel_repo = sub_channel_repo
        self._dyn_renderer = dyn_renderer
        self._sub_list_renderer = sub_list_renderer

    async def get_dyn_image(self, dyn_id: str) -> Optional[bytes]:
        cached = await self._dyn_cache_repo.exists(dyn_id)
        if cached:
            dynamic = pickle.loads(cached)
        else:
            dynamic = await self._api.get_dynamic_by_id(dyn_id)
            if dynamic is None:
                return None
            await self._dyn_cache_repo.save(
                dyn_id, dynamic.header.name, pickle.dumps(dynamic)
            )
        return await self._dyn_renderer.render(dynamic)

    async def get_dyn_image_urls(self, dyn_id: str) -> Optional[List[str]]:
        cached = await self._dyn_cache_repo.exists(dyn_id)
        if cached:
            dynamic = pickle.loads(cached)
        else:
            dynamic = await self._api.get_dynamic_by_id(dyn_id)
            if dynamic is None:
                return None
            await self._dyn_cache_repo.save(
                dyn_id, dynamic.header.name, pickle.dumps(dynamic)
            )
        if dynamic.major and dynamic.major.type == "MAJOR_TYPE_OPUS" and dynamic.major.opus:
            return [pic.url for pic in dynamic.major.opus.pics]
        return []

    async def get_sub_list(self, bot_id: int, group_id: int) -> Optional[bytes]:
        data = await self._sub_channel_repo.list_by_group(bot_id, group_id)
        if not data:
            return None
        return await self._sub_list_renderer.render(data)

    async def get_help_image(self) -> bytes:
        if os.path.exists(_HELP_CACHE_PATH):
            with open(_HELP_CACHE_PATH, "rb") as f:
                return f.read()
        os.makedirs(os.path.dirname(_HELP_CACHE_PATH), exist_ok=True)
        loop = asyncio.get_running_loop()
        img_bytes = await loop.run_in_executor(None, self._render_help_sync)
        with open(_HELP_CACHE_PATH, "wb") as f:
            f.write(img_bytes)
        return img_bytes

    @staticmethod
    def _render_help_sync() -> bytes:
        rows = [
            ("/login", "登录", "SUPERUSER", "扫码登录B站"),
            ("/sub <uid>", "订阅", "管理员", "订阅UP主"),
            ("/unsub <uid>", "删除", "管理员", "取消订阅"),
            ("/live_on <uid>", "—", "管理员", "开启直播推送"),
            ("/live_off <uid>", "—", "管理员", "关闭直播推送"),
            ("/dyn_on <uid>", "—", "管理员", "开启动态推送"),
            ("/dyn_off <uid>", "—", "管理员", "关闭动态推送"),
            ("/bot_on", "—", "管理员", "开启群内推送"),
            ("/bot_off", "—", "管理员", "关闭群内推送"),
            ("/list", "列表", "—", "查看订阅列表"),
            ("/help", "—", "—", "帮助信息"),
            ("/sd <dyn_id>", "—", "—", "查看动态卡片"),
            ("/img <dyn_id>", "—", "—", "提取动态图片"),
        ]

        row_h = 32
        header_h = 38
        title_h = 44
        pad = 20
        w = 680
        h = title_h + header_h + len(rows) * row_h + pad * 2

        surface = skia.Surface(w, h)
        canvas = surface.getCanvas()
        canvas.clear(skia.ColorWHITE)

        typeface = skia.FontMgr().matchFamilyStyleCharacter(
            "Noto Sans CJK SC", skia.FontStyle().Normal(), ["zh", "en"], ord("a"),
        )

        title_font = skia.Font(typeface, 18)
        header_font = skia.Font(typeface, 14)
        body_font = skia.Font(typeface, 13)

        paint = skia.Paint(
            Color=skia.ColorBLACK, StrokeWidth=1, AntiAlias=True,
            Style=skia.Paint.kStroke_Style,
        )

        # grid lines
        cols = [0, 120, 210, 320, w - pad]
        for x in cols:
            canvas.drawLine(x + pad, title_h + pad, x + pad, h - pad, paint)
        for y in range(title_h + pad, h - pad + 1, row_h):
            canvas.drawLine(pad, y, w - pad, y, paint)

        paint.setStyle(skia.Paint.kFill_Style)

        def draw_text(text, x, y, font, r=0, g=0, b=0):
            paint.setARGB(255, r, g, b)
            blob = skia.TextBlob(text, font)
            canvas.drawTextBlob(blob, x + pad + 8, y + 22, paint)

        # title
        draw_text("arielBot 帮助", pad, title_h + pad, title_font, 30, 80, 200)

        # header row
        headers = ("命令", "别名", "权限", "说明")
        for i, col_x in enumerate(cols[:-1]):
            draw_text(headers[i], col_x + pad, title_h + pad, header_font)
        y = title_h + header_h
        canvas.drawLine(pad, y - row_h + pad, w - pad, y - row_h + pad, paint)

        # body
        for row in rows:
            for i, col_x in enumerate(cols[:-1]):
                draw_text(row[i], col_x + pad, y + pad, body_font)
            y += row_h

        skia_img = skia.Image.fromarray(
            canvas.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType),
            colorType=skia.ColorType.kRGBA_8888_ColorType,
        )
        buf = BytesIO()
        skia_img.save(buf)
        return buf.getvalue()