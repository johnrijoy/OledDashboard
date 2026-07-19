"""Reusable animation state machine for the eyes page."""

import random


class EyeAnimator:
    """
    Drives gaze position and blinking for a pair of animated eyes.

    Call `.step(dt)` once per frame to advance the animation, then read
    `.gaze_x`, `.gaze_y` (pupil offset in px) and `.eyelid` (0.0 open ..
    1.0 fully closed) to render the eyes.
    """

    def __init__(self, gaze_range=6):
        self.gaze_range = gaze_range

        self.gaze_x = 0.0
        self.gaze_y = 0.0
        self.target_x = 0.0
        self.target_y = 0.0

        self.eyelid = 0.0  # 0 = open, 1 = closed
        self._blink_state = "open"
        self._blink_timer = 0.0
        self._next_blink = self._roll_next_blink()
        self._double_blink_pending = False

        self._next_gaze_shift = self._roll_next_gaze()

    @staticmethod
    def _roll_next_blink():
        return random.uniform(2.5, 6.0)

    @staticmethod
    def _roll_next_gaze():
        return random.uniform(1.0, 3.0)

    def step(self, dt):
        # Guard against a huge dt after e.g. a page being idle off-screen.
        dt = min(dt, 0.25)
        self._step_gaze(dt)
        self._step_blink(dt)

    def _step_gaze(self, dt):
        self._next_gaze_shift -= dt
        if self._next_gaze_shift <= 0:
            self.target_x = random.uniform(-1, 1) * self.gaze_range
            self.target_y = random.uniform(-1, 1) * self.gaze_range * 0.5
            self._next_gaze_shift = self._roll_next_gaze()

        # Simple exponential ease toward target = smooth idle drifting.
        ease = min(1.0, dt * 4.0)
        self.gaze_x += (self.target_x - self.gaze_x) * ease
        self.gaze_y += (self.target_y - self.gaze_y) * ease

    def _step_blink(self, dt):
        if self._blink_state == "open":
            self._next_blink -= dt
            if self._next_blink <= 0:
                self._blink_state = "closing"
                self._blink_timer = 0.0
        elif self._blink_state == "closing":
            self._blink_timer += dt
            self.eyelid = min(1.0, self._blink_timer / 0.08)
            if self.eyelid >= 1.0:
                self._blink_state = "closed"
                self._blink_timer = 0.0
        elif self._blink_state == "closed":
            self._blink_timer += dt
            if self._blink_timer >= 0.06:
                self._blink_state = "opening"
                self._blink_timer = 0.0
        elif self._blink_state == "opening":
            self._blink_timer += dt
            self.eyelid = max(0.0, 1.0 - self._blink_timer / 0.08)
            if self.eyelid <= 0.0:
                # Occasionally chain a second quick blink.
                if not self._double_blink_pending and random.random() < 0.2:
                    self._double_blink_pending = True
                    self._blink_state = "open"
                    self._next_blink = random.uniform(0.15, 0.3)
                else:
                    self._double_blink_pending = False
                    self._blink_state = "open"
                    self._next_blink = self._roll_next_blink()
