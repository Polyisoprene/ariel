import asyncio
import os
import pickle
import skia
from io import BytesIO
from typing import List, Optional
from arielbot.domain.interfaces.api import BiliContentAPI
from arielbot.domain.interfaces.repository import DynCacheRepository, SubChannelRepository
from arielbot.domain.interfaces.renderer import DynRenderer, SubListRenderer
from arielbot.infrastructure.adapters.renderer import _find_cjk_typeface

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
        header_h = 36
        title_h = 44
        pad = 20
        cols = [0, 130, 220, 340, 660]
        w = 680
        h = title_h + header_h + len(rows) * row_h + pad * 2

        surface = skia.Surface(w, h)
        canvas = surface.getCanvas()
        canvas.clear(skia.ColorWHITE)
        paint = skia.Paint(Color=skia.ColorBLACK, StrokeWidth=1, AntiAlias=True, Style=skia.Paint.kStroke_Style)

        typeface = _find_cjk_typeface()
        title_font = skia.Font(typeface, 18)
        header_font = skia.Font(typeface, 14)
        body_font = skia.Font(typeface, 13)

        # grid lines
        for x in cols:
            canvas.drawLine(x + pad, title_h + pad, x + pad, h - pad, paint)
        for y in range(title_h + pad, h - pad + 1, row_h):
            canvas.drawLine(pad, y, w - pad, y, paint)

        paint.setStyle(skia.Paint.kFill_Style)

        def cell_rect(col_idx, y_offset):
            left = cols[col_idx] + pad
            right = cols[col_idx + 1] + pad if col_idx + 1 < len(cols) else w - pad
            return left, right, y_offset + pad, y_offset + pad + row_h

        def draw_cell(text, col_idx, y_offset, font, r=0, g=0, b=0):
            paint.setARGB(255, r, g, b)
            left, right, top, bottom = cell_rect(col_idx, y_offset)
            cell_w = right - left
            text_w = font.measureText(text)
            metrics = font.getMetrics()
            cell_h = bottom - top
            x_center = left + (cell_w - text_w) / 2
            y_center = top + (cell_h - metrics.fAscent + metrics.fDescent) / 2 - metrics.fDescent
            blob = skia.TextBlob(text, font)
            canvas.drawTextBlob(blob, int(x_center), int(y_center), paint)

        # title
        draw_cell("arielBot 帮助", 0, title_h, title_font, 30, 80, 200)
        y = title_h
        canvas.drawLine(pad, y + pad, w - pad, y + pad, paint)

        # header row
        headers = ("命令", "别名", "权限", "说明")
        y += header_h
        for i in range(4):
            draw_cell(headers[i], i, y, header_font)
        canvas.drawLine(pad, y + pad, w - pad, y + pad, paint)

        # body rows
        y += row_h
        for row in rows:
            for i in range(4):
                draw_cell(row[i], i, y, body_font)
            y += row_h

        skia_img = skia.Image.fromarray(
            canvas.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType),
            colorType=skia.ColorType.kRGBA_8888_ColorType,
        )
        buf = BytesIO()
        skia_img.save(buf)
        return buf.getvalue()