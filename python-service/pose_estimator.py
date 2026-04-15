# import os
# import logging
# import cv2
# import numpy as np
# import mediapipe as mp

# logger = logging.getLogger(__name__)

# mp_pose = mp.solutions.pose

# VISIBILITY_THRESHOLD: float = 0.3

# # ── Stickman colors per fighter (BGR format) ──────────────────────────────────
# FIGHTER_COLORS = [
#     (255, 255, 255),   # Fighter 1 — white
#     (0,   255, 255),   # Fighter 2 — yellow
#     (0,   255,   0),   # Fighter 3 — green
#     (255, 128,   0),   # Fighter 4 — blue
#     (255,   0, 255),   # Fighter 5 — magenta
# ]


# class PoseEstimator:
#     """
#     Wraps multiple MediaPipe Pose instances to track multiple fighters.
#     MediaPipe's single Pose model tracks one dominant person per instance.
#     We run N instances on cropped regions to track N fighters independently.

#     Use as a context manager:
#         with PoseEstimator(max_people=2) as estimator:
#             all_landmarks = estimator.estimate_all(frame)
#     """

#     def __init__(self, max_people: int = 2) -> None:
#         model_complexity = int(os.getenv("MEDIAPIPE_MODEL_COMPLEXITY", "1"))
#         self.max_people = max_people

#         logger.info(
#             "Initialising PoseEstimator — max_people=%d, model_complexity=%d",
#             max_people, model_complexity,
#         )

#         # One Pose instance per fighter slot
#         self.poses = [
#             mp_pose.Pose(
#                 static_image_mode=False,
#                 model_complexity=model_complexity,
#                 smooth_landmarks=True,
#                 min_detection_confidence=0.5,
#                 min_tracking_confidence=0.5,
#             )
#             for _ in range(max_people)
#         ]

#         # Track last known bounding boxes for each fighter
#         self._last_boxes: list[tuple | None] = [None] * max_people

#     def __enter__(self) -> "PoseEstimator":
#         return self

#     def __exit__(self, *args) -> None:
#         self.close()

#     def estimate_all(
#         self, frame: np.ndarray
#     ) -> list[dict[int, dict] | None]:
#         """
#         Estimate poses for all fighters in the frame.
#         Returns a list of landmark dicts (one per fighter slot).
#         None means no person detected in that slot.
#         """
#         rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         h, w = frame.shape[:2]

#         # Step 1 — run full-frame detection on pose[0] to find all people
#         full_result = self.poses[0].process(rgb)

#         # Step 2 — get bounding boxes for each detected person using
#         # segmentation / landmark spread per detected body
#         person_boxes = self._extract_person_boxes(
#             full_result, w, h, frame
#         )

#         results: list[dict[int, dict] | None] = []

#         for i in range(self.max_people):
#             if i >= len(person_boxes):
#                 results.append(None)
#                 continue

#             box = person_boxes[i]
#             x1, y1, x2, y2 = box

#             # Crop frame to this person's bounding box
#             cropped = rgb[y1:y2, x1:x2]
#             if cropped.size == 0:
#                 results.append(None)
#                 continue

#             # Run pose on cropped region
#             pose_result = self.poses[i].process(cropped)

#             if not pose_result.pose_landmarks:
#                 results.append(None)
#                 continue

#             crop_h = y2 - y1
#             crop_w = x2 - x1

#             landmarks: dict[int, dict] = {}
#             for idx, lm in enumerate(pose_result.pose_landmarks.landmark):
#                 # Map coordinates back to full frame space
#                 landmarks[idx] = {
#                     "x": int(lm.x * crop_w) + x1,
#                     "y": int(lm.y * crop_h) + y1,
#                     "visibility": lm.visibility,
#                 }

#             results.append(landmarks)
#             self._last_boxes[i] = box

#         return results

#     def _extract_person_boxes(
#         self,
#         result,
#         w: int,
#         h: int,
#         frame: np.ndarray,
#     ) -> list[tuple[int, int, int, int]]:
#         """
#         Split the frame into left/right halves as a simple but effective
#         way to separate two fighters who are typically on opposite sides.
#         Falls back to full-frame if only one person is detected.
#         """
#         boxes = []

#         if not result.pose_landmarks:
#             return boxes

#         # Get the X centroid of the detected person
#         xs = [
#             lm.x * w
#             for lm in result.pose_landmarks.landmark
#             if lm.visibility >= VISIBILITY_THRESHOLD
#         ]

#         if not xs:
#             return boxes

#         centroid_x = int(np.mean(xs))
#         padding = int(w * 0.1)  # 10% padding on each side

#         # Fighter 1 — left half (person whose centroid is left of center)
#         if centroid_x < w // 2:
#             boxes.append((
#                 0,
#                 0,
#                 min(w, centroid_x + w // 2 + padding),
#                 h,
#             ))
#             # Fighter 2 — right half
#             boxes.append((
#                 max(0, centroid_x + w // 2 - padding),
#                 0,
#                 w,
#                 h,
#             ))
#         else:
#             # Fighter 1 is on the right — swap sides
#             boxes.append((
#                 max(0, centroid_x - w // 2 - padding),
#                 0,
#                 w,
#                 h,
#             ))
#             boxes.append((
#                 0,
#                 0,
#                 min(w, centroid_x - w // 2 + padding),
#                 h,
#             ))

#         return boxes

#     # Keep single-frame estimate for backward compatibility
#     def estimate(self, frame: np.ndarray) -> dict[int, dict] | None:
#         results = self.estimate_all(frame)
#         return results[0] if results else None

#     def close(self) -> None:
#         for pose in self.poses:
#             pose.close()
#         logger.debug("PoseEstimator closed")