"""
System status page: IP, CPU usage/temp, memory, disk, uptime.

Layout and data-gathering are based directly on the original single-page
OLED stats script (Michael Klements / the-diy-life.com, adapted by
Macley(kun)): icon column + PixelOperator text, IP cached for 60s,
uptime read from /proc/uptime (psutil.boot_time() drifts after suspend/
resume), temperature from the thermal_zone0 sysfs file.

Custom fonts are optional. Drop these into oled_dashboard/fonts/ to get
the original icon look:
  - PixelOperator.ttf     https://www.dafont.com/pixel-operator.font
  - lineawesome-webfont.ttf  https://icons8.com/line-awesome
If they're not present, the page falls back to DejaVu / Pillow's default
font and simply omits the icon glyphs.
"""

import os
import socket

import psutil
from PIL import ImageFont

from .base import Page

FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts")

FONT_SZ = 16


def _load_font(*candidates, size=FONT_SZ):
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


FONT = _load_font(
    os.path.join(FONTS_DIR, "PixelOperator.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
)

# Icons are optional -- only used if the icon font actually loaded.
_ICON_PATH = os.path.join(FONTS_DIR, "lineawesome-webfont.ttf")
ICON_FONT = ImageFont.truetype(_ICON_PATH, FONT_SZ) if os.path.exists(_ICON_PATH) else None

ICON_WIFI = chr(61931)
ICON_CPU = chr(62171)
ICON_TEMP = chr(62153)
ICON_MEM = chr(62776)
ICON_DISK = chr(63426)
ICON_TIME = chr(62034)


def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "0.0.0.0"


def get_temp_c():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return float(f.read().strip()) / 1000.0
    except Exception:
        return 0.0


def format_uptime(seconds):
    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24

    minutes %= 60
    hours %= 24

    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}:{minutes:02d}"
    else:
        return f"{minutes}m"


def get_uptime_seconds():
    # /proc/uptime is used instead of psutil.boot_time(): the latter can
    # drift after a suspend/resume cycle on some Pi setups.
    try:
        with open("/proc/uptime", "r") as f:
            return int(float(f.readline().split()[0]))
    except Exception:
        import time
        return int(time.time() - psutil.boot_time())


class StatusPage(Page):
    duration = 10.0
    refresh_interval = 5.0  # data refreshes every ~5s per spec

    IP_RECHECK_SECONDS = 60.0  # IP rarely changes; don't re-resolve every tick

    def __init__(self, width, height):
        super().__init__(width, height)
        self.ip = get_ip()
        self.cpu = 0.0
        self.temp_c = 0.0
        self.mem_pct = 0.0
        self.mem_used_gb = 0.0
        self.mem_total_gb = 0.0
        self.disk_pct = 0
        self.uptime = "0m"

        self._ip_age = 0.0
        # Prime psutil's internal CPU sampler so the first real reading
        # isn't just 0.0.
        psutil.cpu_percent(interval=None)

    def update(self, dt):
        self._ip_age += dt
        if self._ip_age >= self.IP_RECHECK_SECONDS:
            self.ip = get_ip()
            self._ip_age = 0.0

        self.cpu = psutil.cpu_percent(interval=None)
        self.temp_c = get_temp_c()

        vm = psutil.virtual_memory()
        self.mem_pct = vm.percent
        self.mem_used_gb = vm.used / (1024 ** 3)
        self.mem_total_gb = vm.total / (1024 ** 3)

        self.disk_pct = int(psutil.disk_usage("/").percent)
        self.uptime = format_uptime(get_uptime_seconds())

    def draw(self, draw):
        draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

        if ICON_FONT is not None:
            draw.text((1, 0), ICON_WIFI, font=ICON_FONT, fill=255)
            draw.text((1, 16), ICON_CPU, font=ICON_FONT, fill=255)
            draw.text((111, 16), ICON_TEMP, font=ICON_FONT, fill=255)
            draw.text((1, 32), ICON_MEM, font=ICON_FONT, fill=255)
            draw.text((1, 48), ICON_DISK, font=ICON_FONT, fill=255)
            draw.text((111, 48), ICON_TIME, font=ICON_FONT, fill=255)
            label_x = 22
        else:
            # No icon font available -- fall back to plain labels so the
            # page still reads fine without extra font files installed.
            draw.text((0, 0), "IP", font=FONT, fill=255)
            draw.text((0, 16), "CPU", font=FONT, fill=255)
            draw.text((0, 32), "MEM", font=FONT, fill=255)
            draw.text((0, 48), "DSK", font=FONT, fill=255)
            label_x = 34

        draw.text((label_x, 0), self.ip, font=FONT, fill=255)
        draw.text((label_x, 16), f"{self.cpu:.0f}%", font=FONT, fill=255)
        draw.text((self.width - 1, 16), f"{self.temp_c:.1f}C", font=FONT, fill=255, anchor="ra")
        draw.text((label_x, 32), f"{self.mem_pct:.0f}%", font=FONT, fill=255)
        draw.text(
            (self.width - 1, 32),
            f"{self.mem_used_gb:.1f}/{self.mem_total_gb:.0f}G",
            font=FONT,
            fill=255,
            anchor="ra",
        )
        draw.text((label_x, 48), f"{self.disk_pct}%", font=FONT, fill=255)
        draw.text((self.width - 1, 48), self.uptime, font=FONT, fill=255, anchor="ra")
