import cv2
import logging
import tempfile
import os
from typing import Callable, Optional
from pose_estimator import PoseEstimator
from stickman_renderer import StickmanRenderer
from object_detector import ObjectDetector
from effects_renderer import EffectsRenderer

logger = logging.getLogger(__name__)

_CODEC_PREFERENCE = ["avc1", "mp4v"]


def _open_writer(
    output_path: str, fps: float, width: int, height: int
) -> cv2.VideoWriter:
    for codec in _CODEC_PREFERENCE:
        fourcc = cv2.VideoWriter_fourcc(*codec)
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        if writer.isOpened():
            logger.info("VideoWriter opened with codec '%s'", codec)
            return writer
        writer.release()
        logger.warning("Codec '%s' unavailable, trying next...", codec)
    raise RuntimeError(
        f"Could not open VideoWriter with any codec: {_CODEC_PREFERENCE}"
    )


def process_video(
    input_path: str,
    job_id: str,
    progress_callback: Callable[[int], None] | None = None,
) -> str:
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"[{job_id}] Could not open input video: {input_path}")

    fps          = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width        = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height       = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    has_frame_count = total_frames > 0

    logger.info(
        "[%s] Video info — %dx%d @ %.2f fps, ~%d frames",
        job_id, width, height, fps, total_frames,
    )

    output_tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix=f"-{job_id}.mp4"
    )
    output_path = output_tmp.name
    output_tmp.close()

    writer = _open_writer(output_path, fps, width, height)

    # ── Initialise all processors ─────────────────────────────────────────────
    object_detector  = ObjectDetector()
    effects_renderer = EffectsRenderer()
    frame_count      = 0
    prev_landmarks: Optional[dict] = None

    # Scene-level sword flag — once a sword is confirmed in the scene
    # we keep sword effects for the remainder of the video
    scene_has_sword  = False

    with PoseEstimator() as estimator:
        renderer = StickmanRenderer(width, height)

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # 1. Pose estimation on the original frame
                landmarks = estimator.estimate(frame)

                # 2. Object/weapon detection every 5 frames (saves CPU)
                if frame_count % 5 == 0:
                    detection = object_detector.detect(frame)
                    if detection["has_sword"]:
                        scene_has_sword = True

                # 3. Render stickman on blank canvas
                stick_frame = renderer.render(landmarks or {})

                # 4. Trigger effects based on what's detected
                if landmarks:
                    # Sword trail — if sword seen anywhere in scene
                    effects_renderer.detect_and_trigger_sword(
                        landmarks, scene_has_sword
                    )

                    # Punch flash + blood — from wrist velocity
                    # Only trigger punches if no sword (sword takes priority)
                    if not scene_has_sword:
                        effects_renderer.detect_and_trigger_punch(
                            landmarks, prev_landmarks
                        )

                    # Fall dust — from hip drop velocity
                    effects_renderer.detect_and_trigger_fall(
                        landmarks, prev_landmarks
                    )

                # 5. Render all active effects onto the stickman frame
                stick_frame = effects_renderer.render(stick_frame)

                # 6. Write final frame
                writer.write(stick_frame)

                prev_landmarks = landmarks
                frame_count += 1

                # 7. Progress reporting
                if progress_callback and frame_count % 10 == 0:
                    if has_frame_count:
                        pct = int((frame_count / total_frames) * 100)
                        progress_callback(min(pct, 99))
                    else:
                        progress_callback(-1)

        finally:
            cap.release()
            writer.release()

    logger.info("[%s] Processed %d frames", job_id, frame_count)
    return output_path