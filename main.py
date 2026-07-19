"""
Entry point for the OLED dashboard.

Run with:
    python3 main.py
"""

import atexit
import signal
import sys
import time

from display import OLEDDisplay
from page_manager import PageManager
from pages.status import StatusPage
from pages.eyes import EyesPage
from pages.clock import ClockPage

# Main loop tick rate. Each page throttles its own update() via
# refresh_interval, so this just needs to be fast enough for the
# fastest page (eyes @ 10 FPS) plus a little headroom. Frames where
# nothing changed skip the actual I2C write (see PageManager.tick),
# so this doesn't cost much CPU even sitting on status/clock pages.
FRAME_INTERVAL = 1.0 / 30.0


def build_pages(width, height):
    """
    The page order here defines the rotation order:
    Status -> Eyes -> Clock -> Status -> ...

    Adding a new page (e.g. weather, Spotify, Docker status) is just a
    matter of writing a pages/whatever.py that implements Page, and
    appending it to this list -- no changes needed anywhere else.
    """
    return [
        StatusPage(width, height),
        EyesPage(width, height),
        ClockPage(width, height),
    ]


def main():
    oled = OLEDDisplay()
    pages = build_pages(oled.width, oled.height)
    manager = PageManager(pages)

    # Make sure the screen gets blanked on any exit path (Ctrl+C, systemd
    # stop, kill), same as the original single-page script.
    atexit.register(oled.cleanup)

    def _handle_signal(signum, frame):
        sys.exit(0)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    while True:
        frame_start = time.monotonic()

        dirty = manager.tick(oled.draw)
        if dirty:
            oled.show()

        elapsed = time.monotonic() - frame_start
        sleep_time = FRAME_INTERVAL - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)


if __name__ == "__main__":
    main()
