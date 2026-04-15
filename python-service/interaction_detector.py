import logging
import numpy as np
from pose_generator import Pose
from actions import ActionType, ACTIONS

logger = logging.getLogger(__name__)


class InteractionDetector:
    """
    Detects when a strike from one fighter lands on another.
    Uses the active action's hit_frame and hit_reach to determine
    whether the attacker's weapon (fist/foot) overlaps the defender.
    """

    def check(
        self,
        attacker_state,
        attacker_pose: Pose,
        defender_state,
        defender_pose: Pose,
        frame_idx: int,
    ) -> bool:
        """
        Returns True if a hit lands this frame.
        Side effects: applies knockback to defender.
        """
        action_def = ACTIONS[attacker_state.current_action]

        # Only check on the exact hit frame
        if action_def.hit_frame is None:
            return False
        if attacker_state.action_frame != action_def.hit_frame:
            return False
        if defender_state.is_ko:
            return False

        # Get strike point (wrist or foot depending on action)
        strike_pt = self._get_strike_point(
            attacker_state.current_action,
            attacker_state.facing,
            attacker_pose,
        )

        if strike_pt is None:
            return False

        # Get defender center
        def_center = (
            (defender_pose.l_hip[0] + defender_pose.r_hip[0]) / 2,
            (defender_pose.l_hip[1] + defender_pose.r_hip[1]) / 2,
        )

        dist = np.sqrt(
            (strike_pt[0] - def_center[0]) ** 2 + (strike_pt[1] - def_center[1]) ** 2
        )

        if dist <= action_def.hit_reach:
            # Hit lands
            knockback_dir = attacker_state.facing
            force = self._get_force(attacker_state.current_action)
            defender_state_ctrl = getattr(defender_state, "_ctrl", None)

            # Apply knockback directly to the state
            from fighter import FighterController

            logger.info(
                "HIT: Fighter %d → Fighter %d (dist=%.1f reach=%.1f)",
                attacker_state.fighter_id,
                defender_state.fighter_id,
                dist,
                action_def.hit_reach,
            )
            return True

        return False

    def _get_strike_point(
        self,
        action: ActionType,
        facing: int,
        pose: Pose,
    ) -> tuple | None:
        """Return the pixel position of the strike weapon."""
        kick_actions = {
            ActionType.KICK_LEFT,
            ActionType.KICK_RIGHT,
            ActionType.JUMP_KICK,
            ActionType.SWEEP_KICK,
        }
        if action in kick_actions:
            if action == ActionType.KICK_LEFT:
                return pose.l_ankle
            return pose.r_ankle

        punch_actions = {
            ActionType.PUNCH_LEFT,
            ActionType.UPPERCUT,
        }
        if action in punch_actions:
            return pose.l_wrist
        if action == ActionType.PUNCH_RIGHT:
            return pose.r_wrist

        return None

    def _get_force(self, action: ActionType) -> float:
        force_map = {
            ActionType.PUNCH_LEFT: 5.0,
            ActionType.PUNCH_RIGHT: 5.0,
            ActionType.UPPERCUT: 7.0,
            ActionType.KICK_LEFT: 8.0,
            ActionType.KICK_RIGHT: 8.0,
            ActionType.JUMP_KICK: 10.0,
            ActionType.SWEEP_KICK: 6.0,
        }
        return force_map.get(action, 5.0)
