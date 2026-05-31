import asyncio
import skia
from io import BytesIO
from typing import List, Tuple
from dynrender_skia.Core import DynRender
from arielbot.domain.interfaces.renderer import DynRenderer, SubListRenderer


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
    async def render(self, dynamic: object) -> bytes:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._render_sync, dynamic)

    def _render_sync(self, dynamic: object) -> bytes:
        img = DynRender(font_family="Noto Sans CJK SC").run(dynamic)
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