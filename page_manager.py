"""Handles automatic rotation between dashboard pages."""

import time


class PageManager:
    def __init__(self, pages):
        if not pages:
            raise ValueError("PageManager needs at least one page")
        self.pages = pages
        self.index = 0
        self.page_start = time.monotonic()
        self.pages[self.index].on_enter()

    @property
    def current(self):
        return self.pages[self.index]

    def tick(self, draw):
        """
        Advance state, rotate pages if the current one has timed out, and
        draw only when something actually changed.

        Returns True if the caller should push the frame to the physical
        display (i.e. call oled.show()), False if nothing changed and the
        hardware write can be skipped. This mirrors the "only redraw when
        the frame tuple changed" trick from the original single-page
        status script -- it keeps CPU/I2C traffic low even though the main
        loop itself ticks at ~30 FPS to keep the eyes animation smooth.
        """
        now = time.monotonic()
        elapsed = now - self.page_start

        page = self.current
        switched = False
        if elapsed >= page.duration:
            self._advance()
            page = self.current
            switched = True

        updated = page.maybe_update()

        if switched or updated:
            page.draw(draw)
            return True
        return False

    def _advance(self):
        self.current.on_exit()
        self.index = (self.index + 1) % len(self.pages)
        self.page_start = time.monotonic()
        self.current.on_enter()
