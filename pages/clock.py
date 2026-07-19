"""
Digital clock page.

Layout (top to bottom):
  - small date, centered
  - large HH:MM time with a blinking colon, small AM/PM beside it
  - small "<location>  <morning temp>/<night temp>" line

Weather comes from Open-Meteo (https://open-meteo.com), a free API that
needs no key -- fetched with the standard library (urllib) so no extra
dependency is required. It's refreshed roughly every 30 minutes and
cached between fetches; if the Pi has no internet or the request fails,
the temperatures just show as "--" instead of crashing the page.
"""

import json
import os
import time
import urllib.request

from PIL import ImageFont

from .base import Page

try:
    FONT_BIG = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 28
    )
    FONT_SMALL = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 10
    )
except Exception:
    FONT_BIG = ImageFont.load_default()
    FONT_SMALL = ImageFont.load_default()

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

# Edit these for your location (or set the matching environment
# variables) -- these defaults are just an example location.
LOCATION_NAME = os.environ.get("WEATHER_LOCATION_NAME", "Adelaide")
LAT = float(os.environ.get("WEATHER_LAT", "-34.9285"))
LON = float(os.environ.get("WEATHER_LON", "138.6007"))

MORNING_HOUR = 8   # 24h clock, local time at the given location
NIGHT_HOUR = 20


def _text_w(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def fetch_weather(lat, lon, timeout=5):
    """Returns (morning_temp_c, night_temp_c); either may be None on failure."""
    url = (
        f"{WEATHER_URL}?latitude={lat}&longitude={lon}"
        f"&hourly=temperature_2m&timezone=auto&forecast_days=1"
    )
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        times = data["hourly"]["time"]
        temps = data["hourly"]["temperature_2m"]
        morning_temp = night_temp = None
        for t, temp in zip(times, temps):
            hour = int(t[11:13])
            if hour == MORNING_HOUR:
                morning_temp = temp
            elif hour == NIGHT_HOUR:
                night_temp = temp
        return morning_temp, night_temp
    except Exception:
        return None, None


class ClockPage(Page):
    duration = 10.0
    refresh_interval = 0.5  # toggles the colon at 1Hz (on 0.5s / off 0.5s)

    WEATHER_REFRESH_SECONDS = 30 * 60  # weather barely changes minute to minute

    def __init__(self, width, height):
        super().__init__(width, height)
        self.hour_str = "12"
        self.min_str = "00"
        self.ampm = "AM"
        self.date_str = ""
        self.colon_on = True

        self.morning_temp = None
        self.night_temp = None
        # Force a fetch on the very first update() call.
        self._weather_age = self.WEATHER_REFRESH_SECONDS

    def on_enter(self):
        super().on_enter()
        # Always show the colon lit the instant this page becomes visible.
        self.colon_on = True

    def update(self, dt):
        now = time.localtime()
        self.hour_str = time.strftime("%I", now).lstrip("0") or "12"
        self.min_str = time.strftime("%M", now)
        self.ampm = time.strftime("%p", now)
        self.date_str = time.strftime("%a %d %b", now)

        self.colon_on = not self.colon_on

        self._weather_age += dt
        if self._weather_age >= self.WEATHER_REFRESH_SECONDS:
            self.morning_temp, self.night_temp = fetch_weather(LAT, LON)
            self._weather_age = 0.0

    def draw(self, draw):
        draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

        # -- Top: small date, centered --
        dw = _text_w(draw, self.date_str, FONT_SMALL)
        draw.text(((self.width - dw) // 2, 0), self.date_str, font=FONT_SMALL, fill=255)

        # -- Middle: big HH:MM (blinking colon) + small AM/PM --
        hh_w = _text_w(draw, self.hour_str, FONT_BIG)
        colon_w = _text_w(draw, ":", FONT_BIG)
        mm_w = _text_w(draw, self.min_str, FONT_BIG)
        ampm_w = _text_w(draw, self.ampm, FONT_SMALL)

        gap = 4
        total_w = hh_w + colon_w + mm_w + gap + ampm_w
        x = (self.width - total_w) // 2
        y = 14

        draw.text((x, y), self.hour_str, font=FONT_BIG, fill=255)
        x += hh_w
        if self.colon_on:
            draw.text((x, y), ":", font=FONT_BIG, fill=255)
        x += colon_w  # reserve the space even when the colon is blanked,
        draw.text((x, y), self.min_str, font=FONT_BIG, fill=255)  # so digits never shift
        x += mm_w + gap
        draw.text((x, y + 16), self.ampm, font=FONT_SMALL, fill=255)

        # -- Bottom: small location + morning/night temps --
        if self.morning_temp is not None and self.night_temp is not None:
            weather_str = f"{LOCATION_NAME}  {self.morning_temp:.0f}\u00b0/{self.night_temp:.0f}\u00b0"
        else:
            weather_str = f"{LOCATION_NAME}  --\u00b0/--\u00b0"

        ww = _text_w(draw, weather_str, FONT_SMALL)
        draw.text(((self.width - ww) // 2, 54), weather_str, font=FONT_SMALL, fill=255)
