from dataclasses import dataclass, field
from enum import Enum
from typing import Callable
from motion_curves import (
    punch_curve,
    kick_curve,
    block_curve,
    knockback_curve,
    ease_in_out,
    ease_out,
    anticipation_curve,
    lerp,
    clamp,
)


class ActionType(Enum):
    IDLE = "idle"
    WALK = "walk"
    PUNCH_LEFT = "punch_left"
    PUNCH_RIGHT = "punch_right"
    KICK_LEFT = "kick_left"
    KICK_RIGHT = "kick_right"
    BLOCK = "block"
    KNOCKBACK = "knockback"
    JUMP_KICK = "jump_kick"
    UPPERCUT = "uppercut"
    SWEEP_KICK = "sweep_kick"
    DODGE = "dodge"
    TAUNT = "taunt"
    FALL = "fall"
    GETUP = "getup"


@dataclass
class ActionDef:
    """
    Defines a single combat action.

    duration_frames : how many frames the action takes
    can_interrupt   : whether a new action can cut this one short
    hit_frame       : frame index when the strike lands (None = no hit)
    hit_reach       : pixel reach of the strike from fighter center
    curve           : progress → [0,1] easing function
    """

    action_type: ActionType
    duration_frames: int
    can_interrupt: bool = True
    hit_frame: int | None = None
    hit_reach: float = 0.0
    curve: Callable[[float], float] = ease_in_out


# ── Action catalogue ───────────────────────────────────────────────────────────

ACTIONS: dict[ActionType, ActionDef] = {
    ActionType.IDLE: ActionDef(
        ActionType.IDLE,
        duration_frames=999,
        can_interrupt=True,
        curve=ease_in_out,
    ),
    ActionType.WALK: ActionDef(
        ActionType.WALK,
        duration_frames=24,
        can_interrupt=True,
        curve=ease_in_out,
    ),
    ActionType.PUNCH_LEFT: ActionDef(
        ActionType.PUNCH_LEFT,
        duration_frames=18,
        can_interrupt=False,
        hit_frame=9,
        hit_reach=140.0,
        curve=punch_curve,
    ),
    ActionType.PUNCH_RIGHT: ActionDef(
        ActionType.PUNCH_RIGHT,
        duration_frames=18,
        can_interrupt=False,
        hit_frame=9,
        hit_reach=140.0,
        curve=punch_curve,
    ),
    ActionType.KICK_LEFT: ActionDef(
        ActionType.KICK_LEFT,
        duration_frames=26,
        can_interrupt=False,
        hit_frame=13,
        hit_reach=180.0,
        curve=kick_curve,
    ),
    ActionType.KICK_RIGHT: ActionDef(
        ActionType.KICK_RIGHT,
        duration_frames=26,
        can_interrupt=False,
        hit_frame=13,
        hit_reach=180.0,
        curve=kick_curve,
    ),
    ActionType.BLOCK: ActionDef(
        ActionType.BLOCK,
        duration_frames=30,
        can_interrupt=True,
        curve=block_curve,
    ),
    ActionType.KNOCKBACK: ActionDef(
        ActionType.KNOCKBACK,
        duration_frames=22,
        can_interrupt=False,
        curve=knockback_curve,
    ),
    ActionType.JUMP_KICK: ActionDef(
        ActionType.JUMP_KICK,
        duration_frames=36,
        can_interrupt=False,
        hit_frame=18,
        hit_reach=200.0,
        curve=kick_curve,
    ),
    ActionType.UPPERCUT: ActionDef(
        ActionType.UPPERCUT,
        duration_frames=20,
        can_interrupt=False,
        hit_frame=10,
        hit_reach=120.0,
        curve=punch_curve,
    ),
    ActionType.SWEEP_KICK: ActionDef(
        ActionType.SWEEP_KICK,
        duration_frames=28,
        can_interrupt=False,
        hit_frame=14,
        hit_reach=160.0,
        curve=kick_curve,
    ),
    ActionType.DODGE: ActionDef(
        ActionType.DODGE,
        duration_frames=16,
        can_interrupt=False,
        curve=ease_out,
    ),
    ActionType.TAUNT: ActionDef(
        ActionType.TAUNT,
        duration_frames=40,
        can_interrupt=True,
        curve=ease_in_out,
    ),
    ActionType.FALL: ActionDef(
        ActionType.FALL,
        duration_frames=30,
        can_interrupt=False,
        curve=ease_out,
    ),
    ActionType.GETUP: ActionDef(
        ActionType.GETUP,
        duration_frames=36,
        can_interrupt=False,
        curve=ease_in_out,
    ),
}
