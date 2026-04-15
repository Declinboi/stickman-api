import logging
from dataclasses import dataclass, field
from actions import ActionType, ACTIONS, ActionDef
from motion_curves import clamp, lerp

logger = logging.getLogger(__name__)


@dataclass
class FighterState:
    """Runtime state of a single fighter."""

    fighter_id: int
    x: float  # hip center X
    y: float  # hip center Y (ground level)
    facing: int  # 1=right, -1=left
    color: tuple  # BGR render color
    health: float = 100.0
    is_ko: bool = False

    # Action queue
    action_queue: list = field(default_factory=list)

    # Current action
    current_action: ActionType = ActionType.IDLE
    action_frame: int = 0  # frames elapsed in current action
    action_progress: float = 0.0  # 0→1

    # Physics
    vel_x: float = 0.0
    vel_y: float = 0.0
    on_ground: bool = True

    # Trail history for motion blur
    trail: list = field(default_factory=list)
    max_trail: int = 6

    # Hit state
    hit_flash: int = 0  # frames of hit flash remaining
    stagger: int = 0  # frames of stagger remaining


class FighterController:
    """
    Manages a fighter's state machine:
    - Processes the action queue
    - Advances action progress frame by frame
    - Applies physics (knockback velocity, gravity for jumps)
    """

    def __init__(self, state: FighterState, fps: float = 30.0) -> None:
        self.state = state
        self.fps = fps
        self._ground_y = state.y

    def queue_action(self, action: ActionType) -> None:
        """Add an action to the fighter's queue."""
        self.state.action_queue.append(action)

    def update(self, frame_idx: int) -> None:
        """Advance the fighter one frame."""
        s = self.state

        if s.is_ko:
            return

        # ── Advance current action ─────────────────────────────────────────────
        action_def = ACTIONS[s.current_action]
        s.action_frame += 1
        s.action_progress = clamp(
            s.action_frame / max(action_def.duration_frames, 1),
            0.0,
            1.0,
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
                # Return to idle when queue is empty
                s.current_action = ActionType.IDLE
                s.action_frame = 0
                s.action_progress = 0.0

        # ── Apply velocity (knockback / walk) ──────────────────────────────────
        s.x = clamp(s.x + s.vel_x, 80, 10000)
        s.y += s.vel_y

        # Gravity
        if not s.on_ground:
            s.vel_y += 1.2
            if s.y >= self._ground_y:
                s.y = self._ground_y
                s.vel_y = 0.0
                s.on_ground = True

        # Friction
        s.vel_x *= 0.82

        # Decrement flash / stagger
        if s.hit_flash > 0:
            s.hit_flash -= 1
        if s.stagger > 0:
            s.stagger -= 1

        # Record trail point
        s.trail.append((s.x, s.y))
        if len(s.trail) > s.max_trail:
            s.trail.pop(0)

    def apply_knockback(self, direction: int, force: float) -> None:
        """Called when a hit lands on this fighter."""
        s = self.state
        s.vel_x = direction * force
        s.hit_flash = 6
        s.stagger = 4
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
