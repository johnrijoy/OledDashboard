"""Digital clock page: large time, day of week, date."""

import time

from PIL import ImageFont

from .base import Page

try:
    FONT_BIG = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 28
    )
    FONT_SMALL = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12
    )
except Exception:
    FONT_BIG = ImageFont.load_default()
    FONT_SMALL = ImageFont.load_default()


class ClockPage(Page):
    duration = 10.0
    refresh_interval = 1.0

    def __init__(self, width, height):
        super().__init__(width, height)
        self.time_str = "00:00:00"
        self.day_str = ""
        self.date_str = ""

    def update(self, dt):
        now = time.localtime()
        self.time_str = time.strftime("%H:%M:%S", now)
        self.day_str = time.strftime("%A", now)
        self.date_str = time.strftime("%d %b %Y", now)

    def draw(self, draw):
        draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

        bbox = draw.textbbox((0, 0), self.time_str, font=FONT_BIG)
        tw = bbox[2] - bbox[0]
        draw.text(((self.width - tw) // 2, 8), self.time_str, font=FONT_BIG, fill=255)

        bbox = draw.textbbox((0, 0), self.day_str, font=FONT_SMALL)
        dw = bbox[2] - bbox[0]
        draw.text(((self.width - dw) // 2, 42), self.day_str, font=FONT_SMALL, fill=255)

        bbox = draw.textbbox((0, 0), self.date_str, font=FONT_SMALL)
        dw2 = bbox[2] - bbox[0]
        draw.text(((self.width - dw2) // 2, 53), self.date_str, font=FONT_SMALL, fill=255)
