import cv2
import logging
import tempfile
import os
import subprocess
from typing import Callable, Optional
from pose_estimator import PoseEstimator
from stickman_renderer import StickmanRenderer

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
    raise RuntimeError(f"No working codec found from: {_CODEC_PREFERENCE}")


def _remux_for_web(input_path: str, job_id: str) -> str:
    output_path = input_path.replace(".mp4", f"-web-{job_id}.mp4")
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        output_path,
    ]
    logger.info("[%s] Re-encoding for web: %s", job_id, " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("[%s] FFmpeg error: %s", job_id, result.stderr)
        raise RuntimeError(f"FFmpeg remux failed for job {job_id}: {result.stderr}")
    logger.info("[%s] FFmpeg remux complete → %s", job_id, output_path)
    return output_path


def process_video(
    input_path: str,
    job_id: str,
    progress_callback: Callable[[int], None] | None = None,
) -> str:
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"[{job_id}] Could not open video: {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    has_frame_count = total_frames > 0

    logger.info(
        "[%s] %dx%d @ %.2ffps ~%d frames",
        job_id,
        width,
        height,
        fps,
        total_frames,
    )

    output_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f"-{job_id}.mp4")
    output_path = output_tmp.name
    output_tmp.close()

    writer = _open_writer(output_path, fps, width, height)
    frame_count = 0

    with PoseEstimator(max_people=2) as estimator:
        renderer = StickmanRenderer(width, height)

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                all_landmarks = estimator.estimate_all(frame)
                stick_frame = renderer.render_all(all_landmarks)
                writer.write(stick_frame)
                frame_count += 1

                if progress_callback and frame_count % 10 == 0:
                    if has_frame_count:
                        pct = int((frame_count / total_frames) * 100)
                        progress_callback(min(pct, 99))
                    else:
                        progress_callback(-1)

        finally:
            cap.release()
            writer.release()

    logger.info("[%s] OpenCV done — %d frames written", job_id, frame_count)

    web_path = _remux_for_web(output_path, job_id)

    if os.path.exists(output_path):
        os.remove(output_path)
        logger.info("[%s] Cleaned up raw OpenCV temp file", job_id)

    return web_path
