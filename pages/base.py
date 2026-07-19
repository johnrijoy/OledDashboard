"""Common interface every dashboard page implements."""

import time


class Page:
    """
    Base class for all dashboard pages.

    Subclasses override `update(dt)` (recompute state) and `draw()` (render).
    The `dt` argument passed to `update()` is the actual elapsed time (in
    seconds) since this page's last update -- the same idea used by
    sh1106-framework's `State.update(self, dt)` -- so animations (like the
    eyes) can advance by a physically correct amount instead of guessing.

    `duration` (seconds) controls how long the page manager keeps this page
    on screen before rotating to the next one.

    `refresh_interval` (seconds) controls how often `update()` runs, so each
    page can pick its own "frame rate" independent of the others (e.g. the
    status page refreshes every 5s while the eyes animate at 10 FPS).
    """

    duration = 10.0
    refresh_interval = 1.0

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._last_update = 0.0

    def on_enter(self):
        """Called once when the page manager switches to this page."""
        self._last_update = 0.0

    def on_exit(self):
        """Called once when the page manager leaves this page."""
        pass

    def maybe_update(self):
        """
        Run update(dt) only if refresh_interval has elapsed.
        Returns True if update() actually ran (i.e. the page's content may
        have changed and it should be redrawn), False otherwise.
        """
        now = time.monotonic()
        elapsed = now - self._last_update
        if elapsed >= self.refresh_interval:
            self._last_update = now
            self.update(elapsed)
            return True
        return False

    def update(self, dt):
        """Recompute internal state (sensor reads, animation step, etc.)."""
        raise NotImplementedError

    def draw(self, draw):
        """Render onto the given PIL ImageDraw object."""
        raise NotImplementedError
