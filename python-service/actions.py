from dataclasses import dataclass
from enum import Enum
from typing import Callable
from motion_curves import (
    punch_curve,
    kick_curve,
    block_curve,
    knockback_curve,
    ease_in_out,
    ease_out,
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

    # 🔥 NEW: hit window instead of single frame
    hit_start: int | None = None
    hit_end: int | None = None

    hit_reach: float = 0.0

    # 🔥 NEW: priority system
    priority: int = 0

    curve: Callable[[float], float] = ease_in_out


ACTIONS: dict[ActionType, ActionDef] = {
    ActionType.IDLE: ActionDef(ActionType.IDLE, 999),
    ActionType.WALK: ActionDef(ActionType.WALK, 8),
    # 🥊 Punches (fast, low priority)
    ActionType.PUNCH_LEFT: ActionDef(
        ActionType.PUNCH_LEFT,
        duration_frames=12,
        can_interrupt=False,
        hit_start=4,
        hit_end=7,
        hit_reach=110.0,
        priority=1,
        curve=punch_curve,
    ),
    ActionType.PUNCH_RIGHT: ActionDef(
        ActionType.PUNCH_RIGHT,
        duration_frames=12,
        can_interrupt=False,
        hit_start=4,
        hit_end=7,
        hit_reach=110.0,
        priority=1,
        curve=punch_curve,
    ),
    # 🦵 Kicks (medium)
    ActionType.KICK_LEFT: ActionDef(
        ActionType.KICK_LEFT,
        duration_frames=18,
        can_interrupt=False,
        hit_start=7,
        hit_end=11,
        hit_reach=140.0,
        priority=2,
        curve=kick_curve,
    ),
    ActionType.KICK_RIGHT: ActionDef(
        ActionType.KICK_RIGHT,
        duration_frames=18,
        can_interrupt=False,
        hit_start=7,
        hit_end=11,
        hit_reach=140.0,
        priority=2,
        curve=kick_curve,
    ),
    ActionType.BLOCK: ActionDef(
        ActionType.BLOCK,
        duration_frames=18,
        can_interrupt=True,
        priority=3,  # defensive priority
        curve=block_curve,
    ),
    ActionType.KNOCKBACK: ActionDef(
        ActionType.KNOCKBACK,
        duration_frames=16,
        can_interrupt=False,
        curve=knockback_curve,
    ),
    # 💥 Heavy attacks
    ActionType.JUMP_KICK: ActionDef(
        ActionType.JUMP_KICK,
        duration_frames=30,
        can_interrupt=False,
        hit_start=12,
        hit_end=18,
        hit_reach=170.0,
        priority=4,
        curve=kick_curve,
    ),
    ActionType.UPPERCUT: ActionDef(
        ActionType.UPPERCUT,
        duration_frames=14,
        can_interrupt=False,
        hit_start=5,
        hit_end=9,
        hit_reach=120.0,
        priority=5,
        curve=punch_curve,
    ),
    ActionType.SWEEP_KICK: ActionDef(
        ActionType.SWEEP_KICK,
        duration_frames=20,
        can_interrupt=False,
        hit_start=8,
        hit_end=13,
        hit_reach=130.0,
        priority=3,
        curve=kick_curve,
    ),
    ActionType.DODGE: ActionDef(
        ActionType.DODGE,
        duration_frames=10,
        can_interrupt=False,
        priority=6,  # dodge overrides attacks
        curve=ease_out,
    ),
    ActionType.TAUNT: ActionDef(ActionType.TAUNT, 28),
    ActionType.FALL: ActionDef(ActionType.FALL, 22, can_interrupt=False),
    ActionType.GETUP: ActionDef(ActionType.GETUP, 28, can_interrupt=False),
}
