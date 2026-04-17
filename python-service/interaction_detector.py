import logging
import numpy as np
from pose_generator import Pose
from actions import ActionType, ACTIONS

logger = logging.getLogger(__name__)


class InteractionDetector:

    def check(
        self,
        attacker_state,
        attacker_pose: Pose,
        defender_state,
        defender_pose: Pose,
        frame_idx: int,
    ) -> bool:

        action_def = ACTIONS[attacker_state.current_action]
        defender_def = ACTIONS[defender_state.current_action]

        # ── 1. Must be an attack with a hit window ─────────────────────
        if action_def.hit_start is None or action_def.hit_end is None:
            return False

        if not (
            action_def.hit_start <= attacker_state.action_frame <= action_def.hit_end
        ):
            return False

        if defender_state.is_ko:
            return False

        # ── 2. Priority check (prevents double hits) ───────────────────
        if defender_def.priority > action_def.priority:
            return False

        # ── 3. Get strike point ────────────────────────────────────────
        strike_pt = self._get_strike_point(
            attacker_state.current_action,
            attacker_pose,
        )

        if strike_pt is None:
            return False

        # ── 4. Better target point (upper body instead of hips only) ──
        def_center = (
            (defender_pose.neck[0] + defender_pose.l_hip[0] + defender_pose.r_hip[0])
            / 3,
            (defender_pose.neck[1] + defender_pose.l_hip[1] + defender_pose.r_hip[1])
            / 3,
        )

        dx = strike_pt[0] - def_center[0]
        dy = strike_pt[1] - def_center[1]
        dist = np.sqrt(dx * dx + dy * dy)

        if dist > action_def.hit_reach:
            return False

        # ── 5. Correct knockback direction (CRITICAL FIX) ──────────────
        direction = 1 if defender_state.x > attacker_state.x else -1

        logger.info(
            "HIT: F%d → F%d | dist=%.1f reach=%.1f dir=%d",
            attacker_state.fighter_id,
            defender_state.fighter_id,
            dist,
            action_def.hit_reach,
            direction,
        )

        # Store direction for external use
        attacker_state._last_hit_dir = direction

        return True

    def _get_strike_point(
        self,
        action: ActionType,
        pose: Pose,
    ) -> tuple | None:

        if action in {
            ActionType.KICK_LEFT,
            ActionType.SWEEP_KICK,
        }:
            return pose.l_ankle

        if action in {
            ActionType.KICK_RIGHT,
            ActionType.JUMP_KICK,
        }:
            return pose.r_ankle

        if action in {
            ActionType.PUNCH_LEFT,
            ActionType.UPPERCUT,
        }:
            return pose.l_wrist

        if action == ActionType.PUNCH_RIGHT:
            return pose.r_wrist

        return None
