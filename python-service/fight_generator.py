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
    FIGHTER_COLORS,
)
from actions import ActionType, ACTIONS
from motion_curves import clamp

logger = logging.getLogger(__name__)

FPS = 30
FRAME_W = 1280
FRAME_H = 720
FLOOR_Y_R = 0.72
_CODEC_PREF = ["avc1", "mp4v"]


def _open_writer(path, fps, w, h):
    for codec in _CODEC_PREF:
        fw = cv2.VideoWriter_fourcc(*codec)
        wr = cv2.VideoWriter(path, fw, fps, (w, h))
        if wr.isOpened():
            logger.info("VideoWriter: codec '%s'", codec)
            return wr
        wr.release()
    raise RuntimeError("No working video codec found")


def _remux(input_path: str, job_id: str) -> str:
    out = input_path.replace(".mp4", f"-web-{job_id}.mp4")
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
        out,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {r.stderr}")
    return out


def generate_fight(
    description: str,
    job_id: str,
    progress_callback: Callable[[int], None] | None = None,
) -> str:
    """
    Full pipeline:
    1. Parse description → choreography timeline
    2. Build fighter state machines
    3. Simulate frame by frame
    4. Render each frame
    5. Encode output video
    """

    w, h = FRAME_W, FRAME_H
    floor_y = int(h * FLOOR_Y_R)
    ground_y = floor_y - 10

    # ── 1. Choreography ───────────────────────────────────────────────────────
    choreographer = Choreographer(fps=FPS)
    timeline = choreographer.parse(description)

    max_frame = max(
        (a.frame + ACTIONS[a.action].duration_frames for a in timeline), default=FPS * 8
    )
    total_frames = max_frame + FPS * 3

    logger.info(
        "[%s] Total frames: %d (~%.1fs)", job_id, total_frames, total_frames / FPS
    )

    # ── 2. Fighter setup ──────────────────────────────────────────────────────
    f1_state = FighterState(
        fighter_id=1,
        x=w * 0.30,
        y=ground_y,
        facing=1,
        color=FIGHTER_COLORS[0],
    )
    f2_state = FighterState(
        fighter_id=2,
        x=w * 0.70,
        y=ground_y,
        facing=-1,
        color=FIGHTER_COLORS[1],
    )

    f1_ctrl = FighterController(f1_state, fps=FPS)
    f2_ctrl = FighterController(f2_state, fps=FPS)

    f1_state._ctrl = f1_ctrl
    f2_state._ctrl = f2_ctrl

    pose_gen = PoseGenerator(w, h)
    hit_detect = InteractionDetector()
    effects = EffectsRenderer()

    # ── 3. Output video setup ─────────────────────────────────────────────────
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f"-{job_id}.mp4")
    path = tmp.name
    tmp.close()
    writer = _open_writer(path, FPS, w, h)

    # ── 4. Main simulation loop ───────────────────────────────────────────────
    for fi in range(total_frames):

        # Schedule actions from timeline
        for sched in timeline:
            if sched.frame == fi:
                ctrl = f1_ctrl if sched.fighter_id == 1 else f2_ctrl
                ctrl.queue_action(sched.action)

        # Update fighter state machines — pass opponent so they track each other
        f1_ctrl.update(fi, opponent_state=f2_state)
        f2_ctrl.update(fi, opponent_state=f1_state)

        # Generate poses — subtract air_height from root_y so jumps lift the body
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

        # Sync air_height from pose back to state for next frame
        f1_state.air_height = f1_pose.air_height
        f2_state.air_height = f2_pose.air_height

        # Hit detection
        hit1 = hit_detect.check(f1_state, f1_pose, f2_state, f2_pose, fi)
        hit2 = hit_detect.check(f2_state, f2_pose, f1_state, f1_pose, fi)

        if hit1:
            kb_dir = 1 if f2_state.x > f1_state.x else -1
            _HIT_TYPE_MAP = {
                ActionType.UPPERCUT: "uppercut",
                ActionType.JUMP_KICK: "jump_kick",
                ActionType.KICK_LEFT: "kick",
                ActionType.KICK_RIGHT: "kick",
                ActionType.SWEEP_KICK: "sweep",
                ActionType.PUNCH_LEFT: "punch",
                ActionType.PUNCH_RIGHT: "punch",
            }
            hit_type = _HIT_TYPE_MAP.get(f1_state.current_action, "default")
            f2_ctrl.apply_knockback(kb_dir, 9.0, hit_type=hit_type)
            strike_pt = f2_pose.l_hip
            effects.trigger_punch(int(strike_pt[0]), int(strike_pt[1]))
            effects.trigger_blood(int(strike_pt[0]), int(strike_pt[1]), 6)

        if hit2:
            kb_dir = 1 if f1_state.x > f2_state.x else -1
            f1_ctrl.apply_knockback(kb_dir, 9.0)
            strike_pt = f1_pose.l_hip
            effects.trigger_punch(int(strike_pt[0]), int(strike_pt[1]))
            effects.trigger_blood(int(strike_pt[0]), int(strike_pt[1]), 6)

        # ── Render frame ──────────────────────────────────────────────────────
        frame = np.zeros((h, w, 3), dtype=np.uint8)

        draw_background(frame, w, h)

        draw_shadow(frame, f1_pose, floor_y)
        draw_shadow(frame, f2_pose, floor_y)

        draw_trail(frame, f1_state.trail, f1_state.color)
        draw_trail(frame, f2_state.trail, f2_state.color)

        draw_fighter(frame, f1_pose, f1_state.color, h, 1, f1_state.hit_flash)
        draw_fighter(frame, f2_pose, f2_state.color, h, 2, f2_state.hit_flash)

        effects.render(frame)

        writer.write(frame)

        if progress_callback and fi % 10 == 0:
            pct = int((fi / total_frames) * 100)
            progress_callback(min(pct, 99))

    writer.release()
    logger.info("[%s] Render complete — %d frames", job_id, total_frames)

    # ── 5. Remux for web ──────────────────────────────────────────────────────
    web_path = _remux(path, job_id)
    if os.path.exists(path):
        os.remove(path)

    return web_path
