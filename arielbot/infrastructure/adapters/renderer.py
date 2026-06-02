import asyncio
import skia
from io import BytesIO
from typing import Any, List, Tuple
from dynrender_skia.Core import DynRender
from arielbot.domain.interfaces.renderer import DynRenderer, SubListRenderer, HelpRenderer


def _find_cjk_typeface() -> skia.Typeface:
    fm = skia.FontMgr()
    for name in ["Noto Sans CJK SC", "Noto Sans CJK", "Source Han Sans SC",
                 "WenQuanYi Micro Hei", "WenQuanYi Zen Hei", "Microsoft YaHei",
                 "SimHei", "PingFang SC", "Hiragino Sans GB"]:
        tf = fm.matchFamilyStyle(name, skia.FontStyle().Normal())
        if tf and tf.getFamilyName():
            return tf
    return fm.matchFamilyStyle("", skia.FontStyle().Normal())


class SkiaDynRenderer(DynRenderer):
    async def render(self, dynamic: Any) -> bytes:
        img = await DynRender(font_family="Noto Sans CJK SC").run(dynamic)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._to_bytes, img)

    @staticmethod
    def _to_bytes(img: Any) -> bytes:
        skia_img = skia.Image.fromarray(
            img, colorType=skia.ColorType.kRGBA_8888_ColorType
        )
        buf = BytesIO()
        skia_img.save(buf)
        return buf.getvalue()


class SkiaSubListRenderer(SubListRenderer):
    async def render(self, data: List[Tuple[str, str, bool, bool]]) -> bytes:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._render_sync, data)

    def _render_sync(self, data: List[Tuple[str, str, bool, bool]]) -> bytes:
        sub_data = list(data)
        if len(sub_data) <= 8:
            img_height = 540
        else:
            img_height = 60 * (len(sub_data) + 1)

        surface = skia.Surface(1000, img_height)
        canvas = surface.getCanvas()
        canvas.clear(skia.ColorWHITE)

        paint = skia.Paint(
            Color=skia.ColorBLACK,
            StrokeWidth=1,
            AntiAlias=True,
            Style=skia.Paint.kStroke_Style,
        )
        for x in range(250, 1000, 250):
            canvas.drawLine(x, 0, x, img_height, paint)
        for y in range(60, img_height, 60):
            rect = skia.Rect.MakeXYWH(0, 0, 1000, y)
            canvas.drawRect(rect, paint)

        typeface = _find_cjk_typeface()
        paint.setStyle(skia.Paint.Style.kFill_Style)
        font = skia.Font(typeface, 16)
        metrics = font.getMetrics()
        baseline_height = round(abs(metrics.fAscent))

        sub_data.insert(0, ("UID", "昵称", "动态推送", "直播推送"))
        for i, row in enumerate(sub_data):
            for j, cell in enumerate(row):
                if cell == 1:
                    text = "开"
                    paint.setARGB(255, 0, 0, 0)
                elif cell == 0:
                    text = "关"
                    paint.setARGB(255, 255, 0, 0)
                else:
                    paint.setARGB(255, 0, 0, 0)
                    text = str(cell)
                blob = skia.TextBlob(text, font)
                text_len = font.measureText(text)
                canvas.drawTextBlob(
                    blob,
                    125 + 250 * j - int(text_len / 2),
                    30 + i * 60 + int(baseline_height / 2),
                    paint,
                )

        skia_img = skia.Image.fromarray(
            canvas.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType),
            colorType=skia.ColorType.kRGBA_8888_ColorType,
        )
        buf = BytesIO()
        skia_img.save(buf)
        return buf.getvalue()


class SkiaHelpRenderer(HelpRenderer):
    async def render(self) -> bytes:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._render_sync)

    @staticmethod
    def _render_sync() -> bytes:
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

        draw_cell("arielBot 帮助", 0, title_h, title_font, 30, 80, 200)
        y = title_h
        canvas.drawLine(pad, y + pad, w - pad, y + pad, paint)

        headers = ("命令", "别名", "权限", "说明")
        y += header_h
        for i in range(4):
            draw_cell(headers[i], i, y, header_font)
        canvas.drawLine(pad, y + pad, w - pad, y + pad, paint)

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