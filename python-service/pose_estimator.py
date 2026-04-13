import mediapipe as mp
import numpy as np

mp_pose = mp.solutions.pose


class PoseEstimator:
    def __init__(self):
        self.pose = mp_pose.Pose(
            static_image_mode=False,       # video mode — faster
            model_complexity=1,            # 0=lite, 1=full, 2=heavy
            smooth_landmarks=True,         # smooths jitter between frames
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def estimate(self, frame: np.ndarray) -> dict | None:
        """
        Run pose estimation on a single BGR frame.
        Returns a dict of landmark positions or None if no person detected.
        """
        # MediaPipe expects RGB
        rgb = frame[:, :, ::-1]
        result = self.pose.process(rgb)

        if not result.pose_landmarks:
            return None

        h, w = frame.shape[:2]
        landmarks = {}

        for idx, lm in enumerate(result.pose_landmarks.landmark):
            landmarks[idx] = {
                "x": int(lm.x * w),
                "y": int(lm.y * h),
                "visibility": lm.visibility,
            }

        return landmarks

    def close(self):
        self.pose.close()