import logging
from dataclasses import dataclass, field
from actions import ActionType, ACTIONS, ActionDef
from motion_curves import clamp, lerp

logger = logging.getLogger(__name__)


@dataclass
class FighterState:
    """Runtime state of a single fighter."""

    fighter_id: int
    x: float
    y: float
    facing: int
    color: tuple
    health: float = 100.0
    is_ko: bool = False

    action_queue: list = field(default_factory=list)

    current_action: ActionType = ActionType.IDLE
    action_frame: int = 0
    action_progress: float = 0.0

    vel_x: float = 0.0
    vel_y: float = 0.0
    on_ground: bool = True

    air_height: float = 0.0  # pixels off ground (synced from pose each frame)

    trail: list = field(default_factory=list)
    max_trail: int = 8

    hit_flash: int = 0
    stagger: int = 0


class FighterController:
    """
    Manages a fighter's state machine:
    - Processes the action queue
    - Advances action progress frame by frame
    - Applies physics (approach, lunge, jump, knockback)
    """

    IDEAL_FIGHT_DIST = 220  # pixels between hip centers

    def __init__(self, state: FighterState, fps: float = 30.0) -> None:
        self.state = state
        self.fps = fps
        self._ground_y = state.y

    def queue_action(self, action: ActionType) -> None:
        self.state.action_queue.append(action)

    def update(
        self, frame_idx: int, opponent_state: "FighterState | None" = None
    ) -> None:
        s = self.state

        # KO fighter still needs to animate the fall
        if s.is_ko:
            action_def = ACTIONS[s.current_action]
            s.action_frame += 1
            s.action_progress = clamp(
                s.action_frame / max(action_def.duration_frames, 1), 0.0, 1.0
            )
            # Apply residual knockback slide then stop
            s.x = clamp(s.x + s.vel_x, 80, 10000)
            s.vel_x *= 0.75
            return

        # ── Advance current action ────────────────────────────────────────────
        action_def = ACTIONS[s.current_action]
        s.action_frame += 1
        s.action_progress = clamp(
            s.action_frame / max(action_def.duration_frames, 1), 0.0, 1.0
        )

        # ── Transition to next queued action ──────────────────────────────────
        action_done = s.action_frame >= action_def.duration_frames

        if action_done or (action_def.can_interrupt and s.action_queue):
            if s.action_queue:
                next_action = s.action_queue.pop(0)
                s.current_action = next_action
                s.action_frame = 0
                s.action_progress = 0.0
                logger.debug("Fighter %d → %s", s.fighter_id, next_action.value)
            elif action_done and s.current_action != ActionType.IDLE:
                s.current_action = ActionType.IDLE
                s.action_frame = 0
                s.action_progress = 0.0

        # ── Always face the opponent ──────────────────────────────────────────
        if opponent_state and s.stagger == 0:
            s.facing = 1 if opponent_state.x > s.x else -1

        # ── Auto-approach / spacing logic ─────────────────────────────────────
        if opponent_state and s.on_ground and s.stagger == 0:
            dist = abs(opponent_state.x - s.x)
            direction = 1 if opponent_state.x > s.x else -1

            idle_or_walk = s.current_action in (ActionType.IDLE, ActionType.WALK)

            if idle_or_walk:
                if dist > self.IDEAL_FIGHT_DIST + 30:
                    # Too far — walk in
                    s.vel_x = direction * 3.8
                    if s.current_action == ActionType.IDLE:
                        s.current_action = ActionType.WALK
                        s.action_frame = 0
                elif dist < self.IDEAL_FIGHT_DIST - 40:
                    # Too close — back off
                    s.vel_x = -direction * 2.0
                else:
                    # In range — settle to idle
                    if s.current_action == ActionType.WALK:
                        s.current_action = ActionType.IDLE
                        s.action_frame = 0

        # ── Action-driven movement impulses ───────────────────────────────────
        if s.action_frame == 1:  # apply impulse only on first frame of action
            if s.current_action in (
                ActionType.PUNCH_LEFT,
                ActionType.PUNCH_RIGHT,
                ActionType.UPPERCUT,
            ):
                s.vel_x = s.facing * 5.0  # lunge into punch

            elif s.current_action == ActionType.SWEEP_KICK:
                s.vel_x = s.facing * 4.0

            elif s.current_action in (ActionType.KICK_LEFT, ActionType.KICK_RIGHT):
                s.vel_x = s.facing * 3.0

            elif s.current_action == ActionType.JUMP_KICK:
                s.vel_x = s.facing * 7.0  # fly forward
                s.vel_y = -20.0  # launch upward
                s.on_ground = False

            elif s.current_action == ActionType.DODGE:
                s.vel_x = -s.facing * 8.0  # dash backward

            elif s.current_action == ActionType.KNOCKBACK:
                pass  # handled by apply_knockback

        # ── Physics ───────────────────────────────────────────────────────────
        s.x = clamp(s.x + s.vel_x, 80, 10000)
        s.y += s.vel_y

        if not s.on_ground:
            s.vel_y += 1.5  # gravity
            if s.y >= self._ground_y:
                s.y = self._ground_y
                s.vel_y = 0.0
                s.on_ground = True

        # Friction — less in air so jumps feel floaty
        s.vel_x *= 0.78 if s.on_ground else 0.96

        # ── Timers ────────────────────────────────────────────────────────────
        if s.hit_flash > 0:
            s.hit_flash -= 1
        if s.stagger > 0:
            s.stagger -= 1

        # ── Trail ─────────────────────────────────────────────────────────────
        s.trail.append((s.x, s.y - s.air_height))
        if len(s.trail) > s.max_trail:
            s.trail.pop(0)

    def apply_knockback(self, direction: int, force: float) -> None:
        s = self.state
        s.vel_x = direction * force
        s.hit_flash = 8
        s.stagger = 6
        s.health = max(0.0, s.health - 12.0)
        if s.health <= 0:
            s.is_ko = True
            s.action_queue.clear()
            s.current_action = ActionType.FALL
            s.action_frame = 0
            s.action_progress = 0.0
        else:
            s.action_queue.clear()
            s.current_action = ActionType.KNOCKBACK
            s.action_frame = 0
            s.action_progress = 0.0
