import cv2
import numpy as np
import random
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ActiveEffect:
    """Represents a currently-playing effect with a lifetime."""

    kind: str  # punch | sword_trail | blood | fall_dust
    x: int
    y: int
    lifetime: int  # frames remaining
    max_lifetime: int
    color: tuple = (255, 255, 255)
    size: int = 30
    points: list = field(default_factory=list)  # for trail effects
    angle: float = 0.0


class EffectsRenderer:
    """
    Manages and renders visual combat effects on the stickman canvas.

    Effect lifecycle:
      - Effects are spawned by calling trigger_*() methods
      - Each call to render() draws all active effects and decrements lifetimes
      - Expired effects are automatically removed
    """

    def __init__(self) -> None:
        self.active_effects: list[ActiveEffect] = []
        self._prev_wrists: dict[int, tuple[int, int]] = {}
        self._frame_idx: int = 0

    # ── Public trigger methods ────────────────────────────────────────────────

    def trigger_punch(self, x: int, y: int) -> None:
        """Spawn a yellow punch flash effect at (x, y)."""
        self.active_effects.append(
            ActiveEffect(
                kind="punch",
                x=x,
                y=y,
                lifetime=8,
                max_lifetime=8,
                color=(255, 220, 0),
                size=random.randint(25, 45),
                angle=random.uniform(0, 360),
            )
        )
        logger.debug("Punch effect triggered at (%d, %d)", x, y)

    def trigger_sword_trail(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Spawn a sword trail between two wrist positions."""
        self.active_effects.append(
            ActiveEffect(
                kind="sword_trail",
                x=x1,
                y=y1,
                lifetime=6,
                max_lifetime=6,
                color=(180, 230, 255),
                size=3,
                points=[(x1, y1), (x2, y2)],
            )
        )

    def trigger_blood(self, x: int, y: int, count: int = 8) -> None:
        """Spawn blood splat particles at (x, y)."""
        for _ in range(count):
            angle = random.uniform(0, 2 * np.pi)
            speed = random.randint(4, 18)
            tx = int(x + np.cos(angle) * speed * 3)
            ty = int(y + np.sin(angle) * speed * 3)
            self.active_effects.append(
                ActiveEffect(
                    kind="blood",
                    x=x,
                    y=y,
                    lifetime=random.randint(8, 18),
                    max_lifetime=18,
                    color=(0, 0, 220),
                    size=random.randint(2, 6),
                    points=[(x, y), (tx, ty)],
                )
            )

    def trigger_fall_dust(self, x: int, y: int) -> None:
        """Spawn dust cloud effect when a character falls."""
        for _ in range(12):
            angle = random.uniform(np.pi, 2 * np.pi)
            dist = random.randint(10, 40)
            tx = int(x + np.cos(angle) * dist)
            ty = int(y + np.sin(angle) * dist)
            self.active_effects.append(
                ActiveEffect(
                    kind="fall_dust",
                    x=x,
                    y=y,
                    lifetime=random.randint(6, 14),
                    max_lifetime=14,
                    color=(160, 160, 160),
                    size=random.randint(3, 8),
                    points=[(x, y), (tx, ty)],
                )
            )

    # ── Auto-detection helpers ────────────────────────────────────────────────

    def detect_and_trigger_punch(
        self,
        landmarks: dict,
        prev_landmarks: Optional[dict],
    ) -> None:
        """
        Detect punch impacts from wrist velocity using default yellow color.
        If a wrist moves more than 25px between frames, trigger a punch flash.
        """
        if not prev_landmarks:
            return

        for wrist_idx in [15, 16]:
            curr = landmarks.get(wrist_idx)
            prev = prev_landmarks.get(wrist_idx)

            if not curr or not prev:
                continue
            if curr["visibility"] < 0.3 or prev["visibility"] < 0.3:
                continue

            dx = curr["x"] - prev["x"]
            dy = curr["y"] - prev["y"]
            velocity = np.sqrt(dx**2 + dy**2)

            if velocity > 25:
                impact_x = curr["x"] + int(dx * 0.4)
                impact_y = curr["y"] + int(dy * 0.4)
                self.trigger_punch(impact_x, impact_y)
                self.trigger_blood(impact_x, impact_y, count=5)

    def detect_and_trigger_punch_colored(
        self,
        landmarks: dict,
        prev_landmarks: Optional[dict],
        fighter_color: tuple,
    ) -> None:
        """
        Same as detect_and_trigger_punch but uses the fighter's
        own color for the punch flash so each fighter's hits are
        visually distinct.
        """
        if not prev_landmarks:
            return

        for wrist_idx in [15, 16]:
            curr = landmarks.get(wrist_idx)
            prev = prev_landmarks.get(wrist_idx)

            if not curr or not prev:
                continue
            if curr["visibility"] < 0.3 or prev["visibility"] < 0.3:
                continue

            dx = curr["x"] - prev["x"]
            dy = curr["y"] - prev["y"]
            velocity = np.sqrt(dx**2 + dy**2)

            if velocity > 25:
                impact_x = curr["x"] + int(dx * 0.4)
                impact_y = curr["y"] + int(dy * 0.4)

                self.active_effects.append(
                    ActiveEffect(
                        kind="punch",
                        x=impact_x,
                        y=impact_y,
                        lifetime=8,
                        max_lifetime=8,
                        color=fighter_color,  # fighter's own color
                        size=random.randint(25, 45),
                        angle=random.uniform(0, 360),
                    )
                )
                self.trigger_blood(impact_x, impact_y, count=5)

    def detect_and_trigger_fall(
        self,
        landmarks: dict,
        prev_landmarks: Optional[dict],
    ) -> None:
        """
        Detect a fall when the hip landmark drops sharply (>40px downward).
        """
        if not prev_landmarks:
            return

        for hip_idx in [23, 24]:
            curr = landmarks.get(hip_idx)
            prev = prev_landmarks.get(hip_idx)

            if not curr or not prev:
                continue
            if curr["visibility"] < 0.3:
                continue

            drop = curr["y"] - prev["y"]
            if drop > 40:
                ankle = landmarks.get(27) or landmarks.get(28)
                fx = ankle["x"] if ankle else curr["x"]
                fy = ankle["y"] if ankle else curr["y"]
                self.trigger_fall_dust(fx, fy)
                break

    def detect_and_trigger_sword(
        self,
        landmarks: dict,
        has_sword: bool,
    ) -> None:
        """
        If a sword is detected in the scene, draw a sword trail
        between the two wrists of this fighter.
        """
        if not has_sword:
            return

        left_wrist = landmarks.get(15)
        right_wrist = landmarks.get(16)

        if not left_wrist or not right_wrist:
            return
        if left_wrist["visibility"] < 0.3 or right_wrist["visibility"] < 0.3:
            return

        self.trigger_sword_trail(
            left_wrist["x"],
            left_wrist["y"],
            right_wrist["x"],
            right_wrist["y"],
        )

    # ── Main render call ──────────────────────────────────────────────────────

    def render(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw all active effects onto the frame.
        Decrements lifetimes and removes expired effects.
        Returns the modified frame.
        """
        still_alive = []

        for effect in self.active_effects:
            alpha = effect.lifetime / effect.max_lifetime

            if effect.kind == "punch":
                self._draw_punch(frame, effect, alpha)
            elif effect.kind == "sword_trail":
                self._draw_sword_trail(frame, effect, alpha)
            elif effect.kind == "blood":
                self._draw_blood(frame, effect, alpha)
            elif effect.kind == "fall_dust":
                self._draw_dust(frame, effect, alpha)

            effect.lifetime -= 1
            if effect.lifetime > 0:
                still_alive.append(effect)

        self.active_effects = still_alive
        self._frame_idx += 1
        return frame

    # ── Private drawing methods ───────────────────────────────────────────────

    def _draw_punch(
        self,
        frame: np.ndarray,
        effect: ActiveEffect,
        alpha: float,
    ) -> None:
        """Star-burst comic punch flash with optional POW! label."""
        cx, cy = effect.x, effect.y
        size = effect.size
        color = self._scale_color(effect.color, alpha)

        # Outer star rays
        for i in range(8):
            angle = np.radians(effect.angle + i * 45)
            ex = int(cx + np.cos(angle) * size)
            ey = int(cy + np.sin(angle) * size)
            cv2.line(frame, (cx, cy), (ex, ey), color, 2, cv2.LINE_AA)

        # Inner filled circle
        cv2.circle(
            frame,
            (cx, cy),
            max(4, int(size * 0.35)),
            color,
            -1,
            cv2.LINE_AA,
        )

        # POW! text on strong hits
        if alpha > 0.6 and size > 30:
            cv2.putText(
                frame,
                "POW!",
                (cx - 20, cy - size - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2,
                cv2.LINE_AA,
            )

    def _draw_sword_trail(
        self,
        frame: np.ndarray,
        effect: ActiveEffect,
        alpha: float,
    ) -> None:
        """Glowing sword slash trail with sparkle dots."""
        if len(effect.points) < 2:
            return

        p1, p2 = effect.points[0], effect.points[1]
        color = self._scale_color(effect.color, alpha)

        # Three overlapping lines for glow
        cv2.line(frame, p1, p2, color, effect.size + 4, cv2.LINE_AA)
        cv2.line(frame, p1, p2, (255, 255, 255), effect.size, cv2.LINE_AA)
        cv2.line(frame, p1, p2, color, max(1, effect.size - 2), cv2.LINE_AA)

        # Sparkle dots along the trail
        for i in range(6):
            t = i / 5
            sx = int(p1[0] + t * (p2[0] - p1[0]))
            sy = int(p1[1] + t * (p2[1] - p1[1]))
            if random.random() < 0.5:
                cv2.circle(
                    frame,
                    (sx, sy),
                    random.randint(1, 3),
                    (255, 255, 255),
                    -1,
                    cv2.LINE_AA,
                )

    def _draw_blood(
        self,
        frame: np.ndarray,
        effect: ActiveEffect,
        alpha: float,
    ) -> None:
        """Animated blood splatter particle."""
        if len(effect.points) < 2:
            return

        t = 1.0 - (effect.lifetime / effect.max_lifetime)
        p1, p2 = effect.points[0], effect.points[1]
        px = int(p1[0] + t * (p2[0] - p1[0]))
        py = int(p1[1] + t * (p2[1] - p1[1]))

        cv2.circle(
            frame,
            (px, py),
            effect.size,
            self._scale_color(effect.color, alpha),
            -1,
            cv2.LINE_AA,
        )

    def _draw_dust(
        self,
        frame: np.ndarray,
        effect: ActiveEffect,
        alpha: float,
    ) -> None:
        """Fall dust particle — drifts upward and fades out."""
        if len(effect.points) < 2:
            return

        t = 1.0 - (effect.lifetime / effect.max_lifetime)
        p1, p2 = effect.points[0], effect.points[1]
        px = int(p1[0] + t * (p2[0] - p1[0]))
        py = int(p1[1] + t * (p2[1] - p1[1]))

        cv2.circle(
            frame,
            (px, py),
            effect.size,
            self._scale_color(effect.color, alpha),
            -1,
            cv2.LINE_AA,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _scale_color(
        color: tuple,
        alpha: float,
    ) -> tuple[int, int, int]:
        """Scale a BGR color by alpha for smooth fade-out."""
        return tuple(int(c * alpha) for c in color)
