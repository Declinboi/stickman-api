import cv2
import logging
import tempfile
import os
import subprocess
import numpy as np
from typing import Callable

from choreography import Choreographer
from fighter import FighterState, FighterController
from pose_generator import PoseGenerator
from interaction_detector import InteractionDetector
from effects_renderer import EffectsRenderer
from scene_renderer import (
    draw_background,
    draw_shadow,
    draw_trail,
    draw_fighter,
    draw_hud,
    FIGHTER_COLORS,
)
from actions import ActionType, ACTIONS
from motion_curves import clamp

logger = logging.getLogger(__name__)

FPS = 30
FRAME_W = 1280
FRAME_H = 720
FLOOR_Y_RATIO = 0.72
_CODEC_PREF = ["avc1", "mp4v"]


def _open_writer(
    output_path: str, fps: float, width: int, height: int
) -> cv2.VideoWriter:
    for codec in _CODEC_PREF:
        fourcc = cv2.VideoWriter_fourcc(*codec)
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        if writer.isOpened():
            logger.info("VideoWriter opened with codec '%s'", codec)
            return writer
        writer.release()
    raise RuntimeError(f"No working codec found from: {_CODEC_PREF}")


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
        "22",
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
    return output_path


def process_video(
    description: str,
    job_id: str,
    progress_callback: Callable[[int], None] | None = None,
) -> str:
    """
    Main pipeline entry point. Replaces the old video-input-based process_video.
    Accepts a natural-language fight description and produces a synthetic animation.
    """
    w, h = FRAME_W, FRAME_H
    floor_y = int(h * FLOOR_Y_RATIO)
    ground_y = floor_y - 10  # hip center rests just above floor

    # ── 1. Parse description into choreography timeline ────────────────────────
    choreographer = Choreographer(fps=FPS)
    timeline = choreographer.parse(description)

    max_frame = max(
        (a.frame + ACTIONS[a.action].duration_frames for a in timeline),
        default=FPS * 8,
    )
    total_frames = max_frame + FPS * 3  # 3s hold at end
    logger.info(
        "[%s] Total frames: %d (~%.1fs)", job_id, total_frames, total_frames / FPS
    )

    # ── 2. Fighter setup ───────────────────────────────────────────────────────
    f1_state = FighterState(
        fighter_id=1,
        x=w * 0.30,
        y=float(ground_y),
        facing=1,
        color=FIGHTER_COLORS[0],
    )
    f2_state = FighterState(
        fighter_id=2,
        x=w * 0.70,
        y=float(ground_y),
        facing=-1,
        color=FIGHTER_COLORS[1],
    )

    f1_ctrl = FighterController(f1_state, fps=FPS)
    f2_ctrl = FighterController(f2_state, fps=FPS)

    # Back-references so hit resolution can reach the controller
    f1_state._ctrl = f1_ctrl
    f2_state._ctrl = f2_ctrl

    pose_gen = PoseGenerator(w, h)
    hit_detect = InteractionDetector()
    effects = EffectsRenderer()

    # ── 3. Video writer setup ──────────────────────────────────────────────────
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f"-{job_id}.mp4")
    output_path = tmp.name
    tmp.close()
    writer = _open_writer(output_path, FPS, w, h)

    # ── 4. Frame simulation loop ───────────────────────────────────────────────
    try:
        for fi in range(total_frames):

            # Schedule actions that start on this frame
            for sched in timeline:
                if sched.frame == fi:
                    ctrl = f1_ctrl if sched.fighter_id == 1 else f2_ctrl
                    ctrl.queue_action(sched.action)

            # Advance state machines
            f1_ctrl.update(fi, opponent_state=f2_state)
            f2_ctrl.update(fi, opponent_state=f1_state)

            # Generate poses mathematically
            f1_pose = pose_gen.generate(
                f1_state.current_action,
                f1_state.action_progress,
                f1_state.x,
                f1_state.y,
                f1_state.facing,
                fi,
            )
            f2_pose = pose_gen.generate(
                f2_state.current_action,
                f2_state.action_progress,
                f2_state.x,
                f2_state.y,
                f2_state.facing,
                fi,
            )

            # Hit detection and reaction
            hit1 = hit_detect.check(f1_state, f1_pose, f2_state, f2_pose, fi)
            hit2 = hit_detect.check(f2_state, f2_pose, f1_state, f1_pose, fi)

            if hit1:
                kb_dir = 1 if f2_state.x > f1_state.x else -1
                f2_ctrl.apply_knockback(kb_dir, 8.0)
                sx, sy = int(f2_pose.l_hip[0]), int(f2_pose.l_hip[1])
                effects.trigger_punch(sx, sy)
                effects.trigger_blood(sx, sy, 5)

            if hit2:
                kb_dir = 1 if f1_state.x > f2_state.x else -1
                f1_ctrl.apply_knockback(kb_dir, 8.0)
                sx, sy = int(f1_pose.l_hip[0]), int(f1_pose.l_hip[1])
                effects.trigger_punch(sx, sy)
                effects.trigger_blood(sx, sy, 5)

            # ── Render ─────────────────────────────────────────────────────────
            frame = np.zeros((h, w, 3), dtype=np.uint8)

            draw_background(frame, w, h)
            draw_shadow(frame, f1_pose, floor_y)
            draw_shadow(frame, f2_pose, floor_y)
            draw_trail(frame, f1_state.trail, f1_state.color)
            draw_trail(frame, f2_state.trail, f2_state.color)
            draw_fighter(frame, f1_pose, f1_state.color, h, 1, f1_state.hit_flash)
            draw_fighter(frame, f2_pose, f2_state.color, h, 2, f2_state.hit_flash)
            effects.render(frame)
            draw_hud(frame, w, h, f1_state, f2_state)

            if not isinstance(frame, np.ndarray):
                raise RuntimeError(f"[{job_id}] Frame {fi} is not a valid ndarray")

            writer.write(frame)

            if progress_callback and fi % 10 == 0:
                pct = int((fi / total_frames) * 100)
                progress_callback(min(pct, 99))

    finally:
        writer.release()

    logger.info("[%s] Render complete — %d frames written", job_id, total_frames)

    # ── 5. Remux for web playback ──────────────────────────────────────────────
    web_path = _remux_for_web(output_path, job_id)
    if os.path.exists(output_path):
        os.remove(output_path)

    return web_path
