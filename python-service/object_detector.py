# import logging
# import numpy as np
# from ultralytics import YOLO

# logger = logging.getLogger(__name__)

# # YOLO class names we care about — maps COCO label → effect type
# WEAPON_CLASSES = {
#     "knife": "sword",
#     "scissors": "sword",
#     "baseball bat": "sword",
#     "sports ball": "punch",
#     "bottle": "sword",
# }

# # Any detected person interaction within this pixel distance
# # of a wrist is treated as a strike
# STRIKE_DISTANCE = 80


# class ObjectDetector:
#     """
#     Detects objects/weapons in frames using YOLOv8.
#     Falls back gracefully if the model cannot be loaded.
#     """

#     def __init__(self) -> None:
#         try:
#             # yolov8n = nano model — fastest, good enough for weapon detection
#             self.model = YOLO("yolov8n.pt")
#             self.enabled = True
#             logger.info("YOLOv8 object detector initialised")
#         except Exception as e:
#             self.model = None
#             self.enabled = False
#             logger.warning("YOLOv8 unavailable — weapon detection disabled: %s", e)

#     def detect(self, frame: np.ndarray) -> dict:
#         """
#         Run object detection on a single BGR frame.
#         Returns a dict with:
#           - weapons: list of {"type": str, "bbox": (x1,y1,x2,y2), "conf": float}
#           - has_sword: bool
#           - has_projectile: bool
#         """
#         result = {
#             "weapons": [],
#             "has_sword": False,
#             "has_projectile": False,
#         }

#         if not self.enabled or self.model is None:
#             return result

#         try:
#             detections = self.model(frame, verbose=False)[0]

#             for box in detections.boxes:
#                 cls_name = self.model.names[int(box.cls)].lower()
#                 conf = float(box.conf)

#                 if conf < 0.35:
#                     continue

#                 effect_type = WEAPON_CLASSES.get(cls_name)
#                 if not effect_type:
#                     continue

#                 x1, y1, x2, y2 = map(int, box.xyxy[0])
#                 result["weapons"].append(
#                     {
#                         "type": effect_type,
#                         "bbox": (x1, y1, x2, y2),
#                         "conf": conf,
#                         "label": cls_name,
#                     }
#                 )

#                 if effect_type == "sword":
#                     result["has_sword"] = True

#         except Exception as e:
#             logger.warning("Object detection failed on frame: %s", e)

#         return result

#     def get_wrist_positions(self, landmarks: dict) -> list[tuple[int, int]]:
#         """Extract wrist pixel positions from pose landmarks."""
#         wrists = []
#         for idx in [15, 16]:  # LEFT_WRIST, RIGHT_WRIST
#             lm = landmarks.get(idx)
#             if lm and lm["visibility"] >= 0.3:
#                 wrists.append((lm["x"], lm["y"]))
#         return wrists
