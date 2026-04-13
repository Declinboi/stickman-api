import os
import logging
import cv2
import numpy as np
import mediapipe as mp
logger = logging.getLogger(__name__)
mp_pose = mp.solutions.pose
# ── Shared visibility threshold ───────────────────────────────────────────────
# Used in both PoseEstimator and StickmanRenderer so the cutoff is defined once.
VISIBILITY_THRESHOLD: float = 0.3
class PoseEstimator:
    """
    Wraps MediaPipe Pose for single-frame landmark estimation.
    Use as a context manager to guarantee the underlying model is closed:
        with PoseEstimator() as estimator:
            landmarks = estimator.estimate(frame)
    """
    def __init__(self) -> None:
        model_complexity = int(os.getenv("MEDIAPIPE_MODEL_COMPLEXITY", "1"))
        logger.info(
            "Initialising PoseEstimator (model_complexity=%d)", model_complexity
        )
        self.pose = mp_pose.Pose(
            static_image_mode=False,        # video mode — reuses tracking state
            model_complexity=model_complexity,
            smooth_landmarks=True,          # reduces jitter between frames
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
    # ── Context-manager support ───────────────────────────────────────────────
    def __enter__(self) -> "PoseEstimator":
        return self
    def __exit__(self, *args) -> None:
        self.close()
    # ── Public API ────────────────────────────────────────────────────────────
    def estimate(self, frame: np.ndarray) -> dict[int, dict] | None:
        """
        Run pose estimation on a single BGR frame.
        Returns a dict mapping landmark index → {x, y, visibility},
        or None if no person is detected.
        """
        # Use cv2.cvtColor for correct, explicit colour-space conversion.
        # This also handles edge cases like 4-channel BGRA frames gracefully
        # (unlike the raw numpy slice [:, :, ::-1]).
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.pose.process(rgb)
        if not result.pose_landmarks:
            return None
        h, w = frame.shape[:2]
        landmarks: dict[int, dict] = {}
        for idx, lm in enumerate(result.pose_landmarks.landmark):
            landmarks[idx] = {
                "x": int(lm.x * w),
                "y": int(lm.y * h),
                "visibility": lm.visibility,
            }
        return landmarks
    def close(self) -> None:
        self.pose.close()
        logger.debug("PoseEstimator closed")