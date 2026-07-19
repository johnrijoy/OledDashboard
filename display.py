"""
OLED display initialization and helper wrapper.

Uses the Adafruit CircuitPython SSD1306 driver + Pillow for framebuffer
drawing. The reset-pin and rotation handling here are carried over from
the original single-page stats script, since several 0.96" SSD1306
Pi HAT/case boards wire a hardware reset line (commonly D4) and some
mount the display upside-down relative to the case.

Install dependencies on the Pi:
    pip3 install adafruit-circuitpython-ssd1306 adafruit-blinka pillow psutil
"""

import os

import board
import busio
import digitalio
from PIL import Image, ImageDraw
import adafruit_ssd1306

WIDTH = 128
HEIGHT = 64
I2C_ADDR = 0x3C

# Some cases (e.g. the-diy-life.com Pi desktop case) wire a hardware
# reset pin, commonly GPIO D4. Set OLED_RESET_PIN=none in the environment
# if your board doesn't use one.
RESET_PIN_NAME = os.environ.get("OLED_RESET_PIN", "D4")

# Some cases mount the display upside down; set OLED_ROTATION=2 to flip.
ROTATION = int(os.environ.get("OLED_ROTATION", "1"))


def _make_reset_pin():
    if RESET_PIN_NAME.lower() == "none":
        return None
    try:
        pin = getattr(board, RESET_PIN_NAME)
        return digitalio.DigitalInOut(pin)
    except Exception:
        # Board without that GPIO exposed, or reset pin not wired --
        # most SSD1306 breakouts work fine without it.
        return None


class OLEDDisplay:
    """Thin wrapper around the SSD1306 driver providing a persistent Pillow canvas."""

    def __init__(self, width=WIDTH, height=HEIGHT, addr=I2C_ADDR):
        self.width = width
        self.height = height

        i2c = busio.I2C(board.SCL, board.SDA)
        reset_pin = _make_reset_pin()

        if reset_pin is not None:
            self.oled = adafruit_ssd1306.SSD1306_I2C(
                width, height, i2c, addr=addr, reset=reset_pin
            )
        else:
            self.oled = adafruit_ssd1306.SSD1306_I2C(width, height, i2c, addr=addr)

        if ROTATION == 2:
            try:
                self.oled.rotate(2)
            except AttributeError:
                self.oled.rotation = 2

        # Persistent framebuffer image/draw object reused every frame,
        # so pages don't need to allocate a new image each tick.
        self.image = Image.new("1", (width, height))
        self.draw = ImageDraw.Draw(self.image)

        self.oled.fill(0)
        self.oled.show()

    def clear(self):
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

    def show(self):
        self.oled.image(self.image)
        self.oled.show()

    def cleanup(self):
        """Blank the screen on shutdown so it doesn't stay stuck on a frame."""
        try:
            self.clear()
            self.show()
        except Exception:
            pass
