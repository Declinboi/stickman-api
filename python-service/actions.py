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
    action_type: ActionType
    duration_frames: int
    can_interrupt: bool = True
    hit_frame: int | None = None
    hit_reach: float = 0.0
    curve: Callable[[float], float] = ease_in_out


ACTIONS: dict[ActionType, ActionDef] = {
    ActionType.IDLE: ActionDef(
        ActionType.IDLE,
        duration_frames=999,
        can_interrupt=True,
        curve=ease_in_out,
    ),
    ActionType.WALK: ActionDef(
        ActionType.WALK,
        duration_frames=8,  # was 24 — snappier steps
        can_interrupt=True,
        curve=ease_in_out,
    ),
    ActionType.PUNCH_LEFT: ActionDef(
        ActionType.PUNCH_LEFT,
        duration_frames=10,  # was 18 — lightning jab
        can_interrupt=False,
        hit_frame=5,  # was 9
        hit_reach=150.0,
        curve=punch_curve,
    ),
    ActionType.PUNCH_RIGHT: ActionDef(
        ActionType.PUNCH_RIGHT,
        duration_frames=10,
        can_interrupt=False,
        hit_frame=5,
        hit_reach=150.0,
        curve=punch_curve,
    ),
    ActionType.KICK_LEFT: ActionDef(
        ActionType.KICK_LEFT,
        duration_frames=16,  # was 26
        can_interrupt=False,
        hit_frame=8,  # was 13
        hit_reach=190.0,
        curve=kick_curve,
    ),
    ActionType.KICK_RIGHT: ActionDef(
        ActionType.KICK_RIGHT,
        duration_frames=16,
        can_interrupt=False,
        hit_frame=8,
        hit_reach=190.0,
        curve=kick_curve,
    ),
    ActionType.BLOCK: ActionDef(
        ActionType.BLOCK,
        duration_frames=18,  # was 30
        can_interrupt=True,
        curve=block_curve,
    ),
    ActionType.KNOCKBACK: ActionDef(
        ActionType.KNOCKBACK,
        duration_frames=14,  # was 22
        can_interrupt=False,
        curve=knockback_curve,
    ),
    ActionType.JUMP_KICK: ActionDef(
        ActionType.JUMP_KICK,
        duration_frames=28,  # was 36 — still needs time for arc
        can_interrupt=False,
        hit_frame=14,  # was 18
        hit_reach=220.0,
        curve=kick_curve,
    ),
    ActionType.UPPERCUT: ActionDef(
        ActionType.UPPERCUT,
        duration_frames=12,  # was 20
        can_interrupt=False,
        hit_frame=6,  # was 10
        hit_reach=130.0,
        curve=punch_curve,
    ),
    ActionType.SWEEP_KICK: ActionDef(
        ActionType.SWEEP_KICK,
        duration_frames=18,  # was 28
        can_interrupt=False,
        hit_frame=9,  # was 14
        hit_reach=170.0,
        curve=kick_curve,
    ),
    ActionType.DODGE: ActionDef(
        ActionType.DODGE,
        duration_frames=10,  # was 16 — instant dash
        can_interrupt=False,
        curve=ease_out,
    ),
    ActionType.TAUNT: ActionDef(
        ActionType.TAUNT,
        duration_frames=28,  # was 40
        can_interrupt=True,
        curve=ease_in_out,
    ),
    ActionType.FALL: ActionDef(
        ActionType.FALL,
        duration_frames=22,  # keep slow for dramatic effect
        can_interrupt=False,
        curve=ease_out,
    ),
    ActionType.GETUP: ActionDef(
        ActionType.GETUP,
        duration_frames=28,  # was 36
        can_interrupt=False,
        curve=ease_in_out,
    ),
}
