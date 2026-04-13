import cv2
import numpy as np
from pose_estimator import VISIBILITY_THRESHOLD
# ── MediaPipe pose landmark indices ───────────────────────────────────────────
NOSE           = 0
LEFT_SHOULDER  = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW     = 13
RIGHT_ELBOW    = 14
LEFT_WRIST     = 15
RIGHT_WRIST    = 16
LEFT_HIP       = 23
RIGHT_HIP      = 24
LEFT_KNEE      = 25
RIGHT_KNEE     = 26
LEFT_ANKLE     = 27
RIGHT_ANKLE    = 28
# ── Connections that make up the stickman body ────────────────────────────────
STICK_CONNECTIONS: list[tuple[int, int]] = [
    # Head to shoulders
    (NOSE,           LEFT_SHOULDER),
    (NOSE,           RIGHT_SHOULDER),
    # Arms
    (LEFT_SHOULDER,  LEFT_ELBOW),
    (LEFT_ELBOW,     LEFT_WRIST),
    (RIGHT_SHOULDER, RIGHT_ELBOW),
    (RIGHT_ELBOW,    RIGHT_WRIST),
    # Torso
    (LEFT_SHOULDER,  LEFT_HIP),
    (RIGHT_SHOULDER, RIGHT_HIP),
    (LEFT_HIP,       RIGHT_HIP),
    (LEFT_SHOULDER,  RIGHT_SHOULDER),
    # Legs
    (LEFT_HIP,       LEFT_KNEE),
    (LEFT_KNEE,      LEFT_ANKLE),
    (RIGHT_HIP,      RIGHT_KNEE),
    (RIGHT_KNEE,     RIGHT_ANKLE),
]
STICK_COLOR    = (255, 255, 255)   # white stickman
BG_COLOR       = (0,   0,   0)    # black background
LIMB_THICKNESS = 4
JOINT_RADIUS   = 5
class StickmanRenderer:
    """
    Renders a stickman figure onto a blank black canvas.
    HEAD_RADIUS scales with frame height so the head looks proportional
    across different resolutions (e.g. 360p vs 1080p).
    """
    def __init__(self, width: int, height: int) -> None:
        self.width  = width
        self.height = height
        # Scale head radius relative to frame height; clamp to [10, 30]
        self.head_radius = max(10, min(30, height // 40))
    def render(self, landmarks: dict[int, dict]) -> np.ndarray:
        """
        Draw a stickman on a blank black frame using the given landmarks.
        Returns a BGR frame (numpy array).
        """
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:] = BG_COLOR
        if not landmarks:
            return frame
        # ── Draw limb connections ─────────────────────────────────────────────
        for start_idx, end_idx in STICK_CONNECTIONS:
            start = landmarks.get(start_idx)
            end   = landmarks.get(end_idx)
            if not start or not end:
                continue
            if (
                start["visibility"] < VISIBILITY_THRESHOLD
                or end["visibility"] < VISIBILITY_THRESHOLD
            ):
                continue
            cv2.line(
                frame,
                (start["x"], start["y"]),
                (end["x"],   end["y"]),
                STICK_COLOR,
                LIMB_THICKNESS,
                lineType=cv2.LINE_AA,
            )
        # ── Draw joint dots ───────────────────────────────────────────────────
        for lm in landmarks.values():
            if lm["visibility"] < VISIBILITY_THRESHOLD:
                continue
            cv2.circle(
                frame,
                (lm["x"], lm["y"]),
                JOINT_RADIUS,
                STICK_COLOR,
                -1,
                lineType=cv2.LINE_AA,
            )
        # ── Draw head circle around nose ──────────────────────────────────────
        nose = landmarks.get(NOSE)
        if nose and nose["visibility"] >= VISIBILITY_THRESHOLD:
            cv2.circle(
                frame,
                (nose["x"], nose["y"]),
                self.head_radius,
                STICK_COLOR,
                LIMB_THICKNESS,
                lineType=cv2.LINE_AA,
            )
        return frame