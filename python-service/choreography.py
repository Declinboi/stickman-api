import logging
import re
from dataclasses import dataclass
from actions import ActionType

logger = logging.getLogger(__name__)


@dataclass
class ScheduledAction:
    """An action scheduled at a specific frame for a specific fighter."""

    frame: int
    fighter_id: int
    action: ActionType


# ── Keyword → ActionType mapping ──────────────────────────────────────────────

_KEYWORD_MAP: dict[str, ActionType] = {
    # Punches
    "jab": ActionType.PUNCH_LEFT,
    "punch": ActionType.PUNCH_RIGHT,
    "left punch": ActionType.PUNCH_LEFT,
    "right punch": ActionType.PUNCH_RIGHT,
    "left jab": ActionType.PUNCH_LEFT,
    "right jab": ActionType.PUNCH_RIGHT,
    "uppercut": ActionType.UPPERCUT,
    "hook": ActionType.PUNCH_RIGHT,
    # Kicks
    "kick": ActionType.KICK_RIGHT,
    "left kick": ActionType.KICK_LEFT,
    "right kick": ActionType.KICK_RIGHT,
    "sweep": ActionType.SWEEP_KICK,
    "sweep kick": ActionType.SWEEP_KICK,
    "jump kick": ActionType.JUMP_KICK,
    "flying kick": ActionType.JUMP_KICK,
    # Defence
    "block": ActionType.BLOCK,
    "guard": ActionType.BLOCK,
    "dodge": ActionType.DODGE,
    "evade": ActionType.DODGE,
    # Movement
    "walk": ActionType.WALK,
    "advance": ActionType.WALK,
    "step": ActionType.WALK,
    # Misc
    "taunt": ActionType.TAUNT,
    "idle": ActionType.IDLE,
}

# Phrases that identify which fighter is acting
_F1_PATTERNS = [
    r"\bf(?:ighter)?\s*1\b",
    r"\bf1\b",
    r"\bplayer\s*1\b",
    r"\bp1\b",
    r"\bfirst\b",
    r"\bleft\b",
]
_F2_PATTERNS = [
    r"\bf(?:ighter)?\s*2\b",
    r"\bf2\b",
    r"\bplayer\s*2\b",
    r"\bp2\b",
    r"\bsecond\b",
    r"\bright\b",
]


def _detect_fighter(sentence: str) -> int | None:
    """Return 1, 2, or None if no fighter is identified."""
    s = sentence.lower()
    for pat in _F1_PATTERNS:
        if re.search(pat, s):
            return 1
    for pat in _F2_PATTERNS:
        if re.search(pat, s):
            return 2
    return None


def _detect_action(sentence: str) -> ActionType | None:
    s = sentence.lower()
    # Try multi-word phrases first (longest match wins)
    for keyword in sorted(_KEYWORD_MAP, key=len, reverse=True):
        if keyword in s:
            return _KEYWORD_MAP[keyword]
    return None


class Choreographer:
    """
    Parses a natural-language fight description and builds a timeline
    of ScheduledActions.

    Sentences are processed in order. Each sentence advances an implicit
    clock by the duration of the action it describes, creating a
    sequential timeline with slight overlaps for realism.
    """

    def __init__(self, fps: float = 30.0) -> None:
        self.fps = fps

    def parse(self, description: str) -> list[ScheduledAction]:
        """
        Convert a fight description into a list of ScheduledActions.
        Returns actions sorted by frame number.
        """
        sentences = self._split(description)
        timeline: list[ScheduledAction] = []

        # Separate clocks per fighter so they can act simultaneously
        clock: dict[int, int] = {1: 0, 2: 0}

        for sent in sentences:
            fighter_id = _detect_fighter(sent)
            action = _detect_action(sent)

            if action is None:
                continue

            if fighter_id is None:
                # Ambiguous — alternate between fighters
                fighter_id = 1 if (len(timeline) % 2 == 0) else 2

            from actions import ACTIONS

            action_def = ACTIONS[action]
            start_frame = clock[fighter_id]

            timeline.append(
                ScheduledAction(
                    frame=start_frame,
                    fighter_id=fighter_id,
                    action=action,
                )
            )

            # Advance this fighter's clock, with slight overlap (80%)
            _FULL_DURATION = {ActionType.FALL, ActionType.GETUP, ActionType.KNOCKBACK}

            overlap = 1.0 if action in _FULL_DURATION else 0.65
            clock[fighter_id] += int(action_def.duration_frames * overlap)

        if not timeline:
            timeline = self._default_fight()

        logger.info("Choreography: %d actions parsed", len(timeline))
        return sorted(timeline, key=lambda a: a.frame)

    def _split(self, text: str) -> list[str]:
        """Split description into individual sentences/clauses."""
        parts = re.split(r"[.,;!\n]+", text)
        return [p.strip() for p in parts if p.strip()]

    def _default_fight(self) -> list[ScheduledAction]:
        """Fallback choreography when description cannot be parsed."""
        from actions import ACTIONS

        sequence = [
            (1, ActionType.WALK),
            (2, ActionType.WALK),
            (1, ActionType.PUNCH_LEFT),
            (2, ActionType.BLOCK),
            (2, ActionType.KICK_RIGHT),
            (1, ActionType.DODGE),
            (1, ActionType.PUNCH_RIGHT),
            (2, ActionType.KNOCKBACK),
            (1, ActionType.UPPERCUT),
            (2, ActionType.BLOCK),
            (2, ActionType.JUMP_KICK),
            (1, ActionType.KNOCKBACK),
            (1, ActionType.SWEEP_KICK),
            (2, ActionType.FALL),
            (1, ActionType.TAUNT),
        ]

        clock = {1: 0, 2: 0}
        result = []

        for fid, action in sequence:
            result.append(
                ScheduledAction(
                    frame=clock[fid],
                    fighter_id=fid,
                    action=action,
                )
            )
            clock[fid] += int(ACTIONS[action].duration_frames * 0.45)

        return sorted(result, key=lambda a: a.frame)
