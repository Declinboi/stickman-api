import numpy as np
from dataclasses import dataclass
from motion_curves import (
    lerp,
    clamp,
    ease_in_out,
    ease_out,
    punch_curve,
    kick_curve,
    idle_breathe,
    anticipation_curve,
)
from actions import ActionType


@dataclass
class Pose:
    """
    Full 2D body pose in pixel space.
    All positions are (x, y) tuples relative to the frame.
    """

    # Core joints
    head: tuple[float, float] = (0, 0)
    neck: tuple[float, float] = (0, 0)
    l_shoulder: tuple[float, float] = (0, 0)
    r_shoulder: tuple[float, float] = (0, 0)
    l_elbow: tuple[float, float] = (0, 0)
    r_elbow: tuple[float, float] = (0, 0)
    l_wrist: tuple[float, float] = (0, 0)
    r_wrist: tuple[float, float] = (0, 0)
    l_hip: tuple[float, float] = (0, 0)
    r_hip: tuple[float, float] = (0, 0)
    l_knee: tuple[float, float] = (0, 0)
    r_knee: tuple[float, float] = (0, 0)
    l_ankle: tuple[float, float] = (0, 0)
    r_ankle: tuple[float, float] = (0, 0)
    body_lean: float = 0.0  # degrees forward lean
    air_height: float = 0.0  # pixels off ground


class PoseGenerator:
    """
    Generates mathematically defined body poses for each action type.

    All poses are built relative to a fighter's root position
    (center of hips) and scaled to the frame height.

    Facing direction:  1 = facing right,  -1 = facing left
    """

    def __init__(self, frame_width: int, frame_height: int) -> None:
        self.fw = frame_width
        self.fh = frame_height

        # Scale everything relative to frame height
        self.s = frame_height

        # Body segment lengths (as fraction of frame height)
        self.head_r = int(self.s * 0.048)
        self.torso_len = int(self.s * 0.20)
        self.upper_arm = int(self.s * 0.13)
        self.forearm = int(self.s * 0.11)
        self.upper_leg = int(self.s * 0.18)
        self.lower_leg = int(self.s * 0.16)

    def generate(
        self,
        action: ActionType,
        progress: float,  # 0.0 → 1.0 within this action
        root_x: float,  # hip center X
        root_y: float,  # hip center Y
        facing: int,  # 1=right, -1=left
        frame_idx: int,  # absolute frame index for idle cycles
    ) -> Pose:
        """Dispatch to the correct pose generator for this action."""

        fn = self._dispatch.get(action, self._idle)
        return fn(self, progress, root_x, root_y, facing, frame_idx)

    # ── Base stance ────────────────────────────────────────────────────────────

    def _base_stance(
        self,
        root_x: float,
        root_y: float,
        facing: int,
        lean: float = 0.0,
        crouch: float = 0.0,
    ) -> dict:
        """
        Returns a dict of all joint positions for the neutral fighting stance.
        lean  : forward body lean in pixels (positive = toward opponent)
        crouch: downward hip shift in pixels
        """
        f = facing
        ry = root_y + crouch

        # Hip center
        l_hip = (root_x - 20, ry)
        r_hip = (root_x + 20, ry)

        # Shoulders (above hips, leaned forward)
        shoulder_y = ry - self.torso_len
        l_shoulder = (root_x - 22 + lean * f, shoulder_y)
        r_shoulder = (root_x + 22 + lean * f, shoulder_y)

        # Neck and head
        neck = (root_x + lean * f, shoulder_y - 12)
        head = (root_x + lean * f, shoulder_y - 12 - self.head_r * 1.5)

        # Arms — guard position (elbows up, wrists near chin)
        l_elbow = (root_x - 38 + lean * f, shoulder_y + 28)
        r_elbow = (root_x + 38 + lean * f, shoulder_y + 28)
        l_wrist = (root_x - 28 + lean * f, shoulder_y + 2)
        r_wrist = (root_x + 28 + lean * f, shoulder_y + 2)

        # Legs — slight fighting crouch
        l_knee = (root_x - 24, ry + self.upper_leg)
        r_knee = (root_x + 24, ry + self.upper_leg)
        l_ankle = (root_x - 28, ry + self.upper_leg + self.lower_leg)
        r_ankle = (root_x + 32, ry + self.upper_leg + self.lower_leg)

        return dict(
            head=head,
            neck=neck,
            l_shoulder=l_shoulder,
            r_shoulder=r_shoulder,
            l_elbow=l_elbow,
            r_elbow=r_elbow,
            l_wrist=l_wrist,
            r_wrist=r_wrist,
            l_hip=l_hip,
            r_hip=r_hip,
            l_knee=l_knee,
            r_knee=r_knee,
            l_ankle=l_ankle,
            r_ankle=r_ankle,
        )

    def _make_pose(self, joints: dict, lean=0.0, air=0.0) -> Pose:
        return Pose(
            head=joints["head"],
            neck=joints["neck"],
            l_shoulder=joints["l_shoulder"],
            r_shoulder=joints["r_shoulder"],
            l_elbow=joints["l_elbow"],
            r_elbow=joints["r_elbow"],
            l_wrist=joints["l_wrist"],
            r_wrist=joints["r_wrist"],
            l_hip=joints["l_hip"],
            r_hip=joints["r_hip"],
            l_knee=joints["l_knee"],
            r_knee=joints["r_knee"],
            l_ankle=joints["l_ankle"],
            r_ankle=joints["r_ankle"],
            body_lean=lean,
            air_height=air,
        )

    # ── Action pose generators ─────────────────────────────────────────────────

    def _idle(self, t, rx, ry, f, fi) -> Pose:
        breathe = idle_breathe(fi, speed=0.3) * 4
        j = self._base_stance(rx, ry, f, lean=4 * f, crouch=breathe)
        return self._make_pose(j)

    def _walk(self, t, rx, ry, f, fi) -> Pose:
        phase = t * 2 * np.pi
        j = self._base_stance(rx, ry, f, lean=8 * f, crouch=0)
        swing = int(np.sin(phase) * 24)
        # Alternating leg swing
        j["l_knee"] = (j["l_knee"][0], j["l_knee"][1] - max(0, swing))
        j["r_knee"] = (j["r_knee"][0], j["r_knee"][1] - max(0, -swing))
        j["l_ankle"] = (
            j["l_ankle"][0] + max(0, swing) * f,
            j["l_ankle"][1] - max(0, swing) // 2,
        )
        j["r_ankle"] = (
            j["r_ankle"][0] + max(0, -swing) * f,
            j["r_ankle"][1] - max(0, -swing) // 2,
        )
        # Arm counter-swing
        j["l_wrist"] = (
            j["l_wrist"][0] - swing * f // 2,
            j["l_wrist"][1] + abs(swing) // 3,
        )
        j["r_wrist"] = (
            j["r_wrist"][0] + swing * f // 2,
            j["r_wrist"][1] - abs(swing) // 3,
        )
        return self._make_pose(j)

    def _punch(self, t, rx, ry, f, fi, left: bool) -> Pose:
        p = punch_curve(t)
        j = self._base_stance(rx, ry, f, lean=p * 18 * f, crouch=0)
        ext = int(self.upper_arm + self.forearm) * p

        if left:
            # Left arm extends forward toward opponent
            j["l_shoulder"] = (j["l_shoulder"][0], j["l_shoulder"][1])
            j["l_elbow"] = (
                j["l_shoulder"][0] + ext * 0.45 * f,
                j["l_shoulder"][1] + 10 - p * 15,
            )
            j["l_wrist"] = (
                j["l_shoulder"][0] + ext * f,
                j["l_shoulder"][1] + 8 - p * 20,
            )
        else:
            j["r_elbow"] = (
                j["r_shoulder"][0] + ext * 0.45 * f,
                j["r_shoulder"][1] + 10 - p * 15,
            )
            j["r_wrist"] = (
                j["r_shoulder"][0] + ext * f,
                j["r_shoulder"][1] + 8 - p * 20,
            )

        # Slight body rotation into the punch
        rot = p * 12 * f
        j["l_hip"] = (j["l_hip"][0] - rot * 0.3, j["l_hip"][1])
        j["r_hip"] = (j["r_hip"][0] + rot * 0.3, j["r_hip"][1])
        return self._make_pose(j, lean=p * 12)

    def _punch_left(self, t, rx, ry, f, fi) -> Pose:
        return self._punch(t, rx, ry, f, fi, left=True)

    def _punch_right(self, t, rx, ry, f, fi) -> Pose:
        return self._punch(t, rx, ry, f, fi, left=False)

    def _kick(self, t, rx, ry, f, fi, left: bool) -> Pose:
        p = kick_curve(t)
        j = self._base_stance(rx, ry, f, lean=p * 10 * f, crouch=0)

        if left:
            # Chamber knee up, then extend
            chamber = min(p / 0.5, 1.0)
            extend = clamp((p - 0.5) / 0.5, 0.0, 1.0)
            knee_lift = int(self.upper_leg * 0.8 * chamber)
            j["l_knee"] = (
                j["l_knee"][0] + extend * self.upper_leg * 0.7 * f,
                j["l_knee"][1] - knee_lift,
            )
            j["l_ankle"] = (
                j["l_ankle"][0] + extend * (self.upper_leg + self.lower_leg) * 0.9 * f,
                j["l_ankle"][1] - knee_lift * 0.4,
            )
            # Balance: right leg bears weight
            j["r_knee"] = (j["r_knee"][0], j["r_knee"][1] + 10)
            # Arms out for balance
            j["l_wrist"] = (j["l_wrist"][0] - 20 * f, j["l_wrist"][1] - 10)
            j["r_wrist"] = (j["r_wrist"][0] + 20 * f, j["r_wrist"][1] - 10)
        else:
            chamber = min(p / 0.5, 1.0)
            extend = clamp((p - 0.5) / 0.5, 0.0, 1.0)
            knee_lift = int(self.upper_leg * 0.8 * chamber)
            j["r_knee"] = (
                j["r_knee"][0] + extend * self.upper_leg * 0.7 * f,
                j["r_knee"][1] - knee_lift,
            )
            j["r_ankle"] = (
                j["r_ankle"][0] + extend * (self.upper_leg + self.lower_leg) * 0.9 * f,
                j["r_ankle"][1] - knee_lift * 0.4,
            )
            j["l_knee"] = (j["l_knee"][0], j["l_knee"][1] + 10)
            j["l_wrist"] = (j["l_wrist"][0] - 20 * f, j["l_wrist"][1] - 10)
            j["r_wrist"] = (j["r_wrist"][0] + 20 * f, j["r_wrist"][1] - 10)

        return self._make_pose(j, lean=p * 8)

    def _kick_left(self, t, rx, ry, f, fi) -> Pose:
        return self._kick(t, rx, ry, f, fi, left=True)

    def _kick_right(self, t, rx, ry, f, fi) -> Pose:
        return self._kick(t, rx, ry, f, fi, left=False)

    def _block(self, t, rx, ry, f, fi) -> Pose:
        p = block_curve(t)
        j = self._base_stance(rx, ry, f, lean=-6 * f, crouch=p * 10)
        # Both arms cross in front of face
        guard = int(p * 30)
        j["l_elbow"] = (j["l_shoulder"][0] + 10 * f, j["l_shoulder"][1] + 14)
        j["r_elbow"] = (j["r_shoulder"][0] - 10 * f, j["r_shoulder"][1] + 14)
        j["l_wrist"] = (j["l_shoulder"][0] + 18 * f, j["l_shoulder"][1] - guard)
        j["r_wrist"] = (j["r_shoulder"][0] + 10 * f, j["r_shoulder"][1] - guard)
        return self._make_pose(j)

    def _knockback(self, t, rx, ry, f, fi) -> Pose:
        p = ease_out(t)
        j = self._base_stance(rx, ry, f, lean=-p * 30 * f, crouch=p * 15)
        # Head snaps back
        j["head"] = (j["head"][0] - p * 20 * f, j["head"][1])
        j["neck"] = (j["neck"][0] - p * 15 * f, j["neck"][1])
        # Arms fly back
        j["l_wrist"] = (j["l_wrist"][0] - p * 25 * f, j["l_wrist"][1] + p * 15)
        j["r_wrist"] = (j["r_wrist"][0] - p * 25 * f, j["r_wrist"][1] + p * 15)
        return self._make_pose(j, lean=-p * 20)

    def _jump_kick(self, t, rx, ry, f, fi) -> Pose:
        # Parabolic jump arc
        air = int(np.sin(t * np.pi) * self.fh * 0.22)
        p = kick_curve(t)
        j = self._base_stance(rx, ry - air, f, lean=p * 15 * f)

        # Both legs tuck then extend
        if t < 0.5:
            tuck = t / 0.5
            j["l_knee"] = (j["l_knee"][0], j["l_knee"][1] - int(tuck * 50))
            j["r_knee"] = (j["r_knee"][0], j["r_knee"][1] - int(tuck * 50))
            j["l_ankle"] = (j["l_ankle"][0], j["l_ankle"][1] - int(tuck * 60))
            j["r_ankle"] = (j["r_ankle"][0], j["r_ankle"][1] - int(tuck * 60))
        else:
            ext = (t - 0.5) / 0.5
            j["r_knee"] = (
                j["r_knee"][0] + int(ext * self.upper_leg * f),
                j["r_knee"][1] - 20,
            )
            j["r_ankle"] = (
                j["r_ankle"][0] + int(ext * (self.upper_leg + self.lower_leg) * f),
                j["r_ankle"][1] - 10,
            )

        return self._make_pose(j, air=air)

    def _uppercut(self, t, rx, ry, f, fi) -> Pose:
        p = punch_curve(t)
        j = self._base_stance(rx, ry, f, lean=p * 8 * f, crouch=-p * 20)
        # Rising punch — arm goes from low to high
        ext = int((self.upper_arm + self.forearm) * p)
        j["r_elbow"] = (j["r_shoulder"][0] + 5 * f, j["r_shoulder"][1] + 20 - p * 40)
        j["r_wrist"] = (j["r_shoulder"][0] + 15 * f, j["r_shoulder"][1] + 30 - p * 80)
        return self._make_pose(j, lean=p * 10)

    def _sweep_kick(self, t, rx, ry, f, fi) -> Pose:
        p = kick_curve(t)
        j = self._base_stance(rx, ry, f, lean=p * 5 * f, crouch=p * 20)
        # Low sweeping leg
        j["l_knee"] = (
            j["l_knee"][0] + p * self.upper_leg * 0.8 * f,
            j["l_knee"][1] + 15,
        )
        j["l_ankle"] = (
            j["l_ankle"][0] + p * (self.upper_leg + self.lower_leg) * 0.85 * f,
            j["l_ankle"][1] + 10,
        )
        return self._make_pose(j)

    def _dodge(self, t, rx, ry, f, fi) -> Pose:
        p = ease_out(t)
        side = -f  # dodge away from opponent
        j = self._base_stance(rx, ry, f, lean=p * 20 * side, crouch=p * 12)
        return self._make_pose(j)

    def _taunt(self, t, rx, ry, f, fi) -> Pose:
        wave = np.sin(t * np.pi * 4) * 20
        j = self._base_stance(rx, ry, f, lean=0, crouch=0)
        j["r_wrist"] = (j["r_wrist"][0] + 30 * f, j["r_wrist"][1] - 40 + wave)
        j["r_elbow"] = (j["r_elbow"][0] + 20 * f, j["r_elbow"][1] - 20)
        return self._make_pose(j)

    def _fall(self, t, rx, ry, f, fi) -> Pose:
        p = ease_out(t)
        j = self._base_stance(rx, ry + p * 40, f, lean=-p * 50 * f, crouch=p * 30)
        j["l_knee"] = (j["l_knee"][0], j["l_knee"][1] - int(p * 30))
        j["r_knee"] = (j["r_knee"][0], j["r_knee"][1] - int(p * 20))
        j["l_ankle"] = (j["l_ankle"][0], j["l_ankle"][1] + int(p * 10))
        j["r_ankle"] = (j["r_ankle"][0], j["r_ankle"][1] - int(p * 10))
        return self._make_pose(j, lean=-p * 40)

    def _getup(self, t, rx, ry, f, fi) -> Pose:
        p = ease_out(t)
        crouch = (1.0 - p) * 35
        j = self._base_stance(rx, ry, f, lean=(1.0 - p) * -20 * f, crouch=crouch)
        return self._make_pose(j)

    # ── Dispatch table ─────────────────────────────────────────────────────────

    _dispatch = {
        ActionType.IDLE: _idle,
        ActionType.WALK: _walk,
        ActionType.PUNCH_LEFT: _punch_left,
        ActionType.PUNCH_RIGHT: _punch_right,
        ActionType.KICK_LEFT: _kick_left,
        ActionType.KICK_RIGHT: _kick_right,
        ActionType.BLOCK: _block,
        ActionType.KNOCKBACK: _knockback,
        ActionType.JUMP_KICK: _jump_kick,
        ActionType.UPPERCUT: _uppercut,
        ActionType.SWEEP_KICK: _sweep_kick,
        ActionType.DODGE: _dodge,
        ActionType.TAUNT: _taunt,
        ActionType.FALL: _fall,
        ActionType.GETUP: _getup,
    }
