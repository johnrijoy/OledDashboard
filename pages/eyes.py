"""Animated eyes page - gives the dashboard some personality."""

from .base import Page
from animations import EyeAnimator


class EyesPage(Page):
    duration = 13.0
    refresh_interval = 1.0 / 10.0  # ~10 FPS per spec

    EYE_W = 34
    EYE_H = 34
    EYE_GAP = 12
    PUPIL_R = 8

    def __init__(self, width, height):
        super().__init__(width, height)
        self.animator = EyeAnimator(gaze_range=8)

    def update(self, dt):
        self.animator.step(dt)

    def draw(self, draw):
        draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

        cy = self.height // 2
        left_cx = self.width // 2 - self.EYE_GAP // 2 - self.EYE_W // 2
        right_cx = self.width // 2 + self.EYE_GAP // 2 + self.EYE_W // 2

        for cx in (left_cx, right_cx):
            self._draw_eye(draw, cx, cy)

    def _draw_eye(self, draw, cx, cy):
        eyelid = self.animator.eyelid  # 0 open .. 1 closed
        open_h = max(2, self.EYE_H * (1.0 - eyelid))

        top = cy - open_h / 2
        bottom = cy + open_h / 2
        left = cx - self.EYE_W / 2
        right = cx + self.EYE_W / 2

        draw.rounded_rectangle((left, top, right, bottom), radius=8, outline=255, fill=0)

        if eyelid < 0.85:
            r = self.PUPIL_R * (1.0 - eyelid * 0.6)
            px = cx + self.animator.gaze_x
            py = cy + self.animator.gaze_y
            px = max(left + r, min(right - r, px))
            py = max(top + r, min(bottom - r, py))
            draw.ellipse((px - r, py - r, px + r, py + r), outline=255, fill=255)
