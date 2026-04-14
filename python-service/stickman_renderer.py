import cv2
import numpy as np
from pose_estimator import VISIBILITY_THRESHOLD, FIGHTER_COLORS

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

STICK_CONNECTIONS: list[tuple[int, int]] = [
    (NOSE,           LEFT_SHOULDER),
    (NOSE,           RIGHT_SHOULDER),
    (LEFT_SHOULDER,  LEFT_ELBOW),
    (LEFT_ELBOW,     LEFT_WRIST),
    (RIGHT_SHOULDER, RIGHT_ELBOW),
    (RIGHT_ELBOW,    RIGHT_WRIST),
    (LEFT_SHOULDER,  LEFT_HIP),
    (RIGHT_SHOULDER, RIGHT_HIP),
    (LEFT_HIP,       RIGHT_HIP),
    (LEFT_SHOULDER,  RIGHT_SHOULDER),
    (LEFT_HIP,       LEFT_KNEE),
    (LEFT_KNEE,      LEFT_ANKLE),
    (RIGHT_HIP,      RIGHT_KNEE),
    (RIGHT_KNEE,     RIGHT_ANKLE),
]

BG_COLOR       = (0, 0, 0)
LIMB_THICKNESS = 4
JOINT_RADIUS   = 5


class StickmanRenderer:
    """
    Renders multiple colored stickman fighters on a single black canvas.
    Each fighter index maps to a unique color from FIGHTER_COLORS.
    """

    def __init__(self, width: int, height: int) -> None:
        self.width  = width
        self.height = height
        self.head_radius = max(10, min(30, height // 40))

    def render_all(
        self,
        all_landmarks: list[dict[int, dict] | None],
    ) -> np.ndarray:
        """
        Render all fighters onto a single black canvas.
        Each fighter gets a unique color from FIGHTER_COLORS.
        Returns a BGR frame.
        """
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:] = BG_COLOR

        for fighter_idx, landmarks in enumerate(all_landmarks):
            if not landmarks:
                continue

            color = FIGHTER_COLORS[fighter_idx % len(FIGHTER_COLORS)]
            self._draw_fighter(frame, landmarks, color, fighter_idx + 1)

        return frame

    def _draw_fighter(
        self,
        frame: np.ndarray,
        landmarks: dict[int, dict],
        color: tuple[int, int, int],
        fighter_number: int,
    ) -> None:
        """Draw a single colored stickman onto the frame."""

        # ── Limbs ─────────────────────────────────────────────────────────────
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
                color,
                LIMB_THICKNESS,
                lineType=cv2.LINE_AA,
            )

        # ── Joints ────────────────────────────────────────────────────────────
        for lm in landmarks.values():
            if lm["visibility"] < VISIBILITY_THRESHOLD:
                continue
            cv2.circle(
                frame,
                (lm["x"], lm["y"]),
                JOINT_RADIUS,
                color,
                -1,
                lineType=cv2.LINE_AA,
            )

        # ── Head ──────────────────────────────────────────────────────────────
        nose = landmarks.get(NOSE)
        if nose and nose["visibility"] >= VISIBILITY_THRESHOLD:
            cv2.circle(
                frame,
                (nose["x"], nose["y"]),
                self.head_radius,
                color,
                LIMB_THICKNESS,
                lineType=cv2.LINE_AA,
            )

        # ── Fighter number label ───────────────────────────────────────────────
        # Small colored label above the head so fighters are clearly identified
        if nose and nose["visibility"] >= VISIBILITY_THRESHOLD:
            label_x = nose["x"] - 8
            label_y = nose["y"] - self.head_radius - 8
            cv2.putText(
                frame,
                f"P{fighter_number}",
                (label_x, label_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
                cv2.LINE_AA,
            )

    # Backward-compatible single render
    def render(self, landmarks: dict[int, dict]) -> np.ndarray:
        return self.render_all([landmarks])