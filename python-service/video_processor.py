import cv2
import tempfile
import os
from pose_estimator import PoseEstimator
from stickman_renderer import StickmanRenderer


def process_video(input_path: str, job_id: str, progress_callback=None) -> str:
    """
    Process a video file:
    1. Read frames from input
    2. Run pose estimation on each frame
    3. Render stickman on blank canvas
    4. Write frames to output video
    Returns path to the output video file.
    """
    cap = cv2.VideoCapture(input_path)

    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {input_path}")

    # Read video properties
    fps        = cap.get(cv2.CAP_PROP_FPS) or 30
    width      = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height     = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Output temp file
    output_tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix=f"-{job_id}.mp4"
    )
    output_path = output_tmp.name
    output_tmp.close()

    # MP4V codec for output
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    estimator = PoseEstimator()
    renderer  = StickmanRenderer(width, height)

    frame_count = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # 1. Estimate pose
            landmarks = estimator.estimate(frame)

            # 2. Render stickman (blank frame if no person detected)
            stick_frame = renderer.render(landmarks or {})

            # 3. Write to output
            writer.write(stick_frame)

            frame_count += 1

            # Report progress every 10 frames
            if progress_callback and frame_count % 10 == 0:
                progress = int((frame_count / max(total_frames, 1)) * 100)
                progress_callback(min(progress, 99))  # cap at 99 until fully done

    finally:
        cap.release()
        writer.release()
        estimator.close()

    return output_path