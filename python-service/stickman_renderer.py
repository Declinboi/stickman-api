import cv2
import numpy as np

# MediaPipe pose landmark indices
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

# Connections that make up the stickman body
STICK_CONNECTIONS = [
    # Head to shoulders
    (NOSE, LEFT_SHOULDER),
    (NOSE, RIGHT_SHOULDER),
    # Shoulders to elbows to wrists (arms)
    (LEFT_SHOULDER,  LEFT_ELBOW),
    (LEFT_ELBOW,     LEFT_WRIST),
    (RIGHT_SHOULDER, RIGHT_ELBOW),
    (RIGHT_ELBOW,    RIGHT_WRIST),
    # Shoulders to hips (torso)
    (LEFT_SHOULDER,  LEFT_HIP),
    (RIGHT_SHOULDER, RIGHT_HIP),
    (LEFT_HIP,       RIGHT_HIP),
    (LEFT_SHOULDER,  RIGHT_SHOULDER),
    # Hips to knees to ankles (legs)
    (LEFT_HIP,   LEFT_KNEE),
    (LEFT_KNEE,  LEFT_ANKLE),
    (RIGHT_HIP,  RIGHT_KNEE),
    (RIGHT_KNEE, RIGHT_ANKLE),
]

STICK_COLOR = (255, 255, 255)  # white stickman
BG_COLOR    = (0, 0, 0)        # black background
HEAD_RADIUS = 18
LIMB_THICKNESS = 4
JOINT_RADIUS   = 5


class StickmanRenderer:
    def __init__(self, width: int, height: int):
        self.width  = width
        self.height = height

    def render(self, landmarks: dict) -> np.ndarray:
        """
        Draw a stickman on a blank black frame using the given landmarks.
        Returns a BGR frame.
        """
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:] = BG_COLOR

        if not landmarks:
            return frame

        # Draw limb connections
        for start_idx, end_idx in STICK_CONNECTIONS:
            start = landmarks.get(start_idx)
            end   = landmarks.get(end_idx)

            if not start or not end:
                continue

            # Skip low-confidence landmarks
            if start["visibility"] < 0.3 or end["visibility"] < 0.3:
                continue

            cv2.line(
                frame,
                (start["x"], start["y"]),
                (end["x"],   end["y"]),
                STICK_COLOR,
                LIMB_THICKNESS,
                lineType=cv2.LINE_AA,
            )

        # Draw joint dots
        for idx, lm in landmarks.items():
            if lm["visibility"] < 0.3:
                continue
            cv2.circle(
                frame,
                (lm["x"], lm["y"]),
                JOINT_RADIUS,
                STICK_COLOR,
                -1,
                lineType=cv2.LINE_AA,
            )

        # Draw head circle around nose
        nose = landmarks.get(NOSE)
        if nose and nose["visibility"] >= 0.3:
            cv2.circle(
                frame,
                (nose["x"], nose["y"]),
                HEAD_RADIUS,
                STICK_COLOR,
                LIMB_THICKNESS,
                lineType=cv2.LINE_AA,
            )

        return frame