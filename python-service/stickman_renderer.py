import cv2
import numpy as np
from pose_estimator import VISIBILITY_THRESHOLD, FIGHTER_COLORS

# MediaPipe landmark indices
NOSE = 0
LEFT_EYE = 2
RIGHT_EYE = 5
LEFT_EAR = 7
RIGHT_EAR = 8
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28
LEFT_FOOT = 31
RIGHT_FOOT = 32
BG_COLOR = (0, 0, 0)


def _pt(landmarks: dict, idx: int):
    lm = landmarks.get(idx)
    if lm and lm["visibility"] >= VISIBILITY_THRESHOLD:
        return (lm["x"], lm["y"])
    return None


def _midpoint(a, b):
    if a and b:
        return ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)
    return a or b


def _dist(a, b):
    if not a or not b:
        return 0
    return int(np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))


def _draw_capsule(frame, p1, p2, color, thickness):
    if not p1 or not p2:
        return
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = max(1, np.sqrt(dx**2 + dy**2))
    px = -dy / length
    py = dx / length
    half = thickness / 2.0
    c1 = (int(p1[0] + px * half), int(p1[1] + py * half))
    c2 = (int(p1[0] - px * half), int(p1[1] - py * half))
    c3 = (int(p2[0] - px * half), int(p2[1] - py * half))
    c4 = (int(p2[0] + px * half), int(p2[1] + py * half))
    pts = np.array([c1, c2, c3, c4], dtype=np.int32)
    cv2.fillPoly(frame, [pts], color)
    cv2.circle(frame, p1, int(half), color, -1, cv2.LINE_AA)
    cv2.circle(frame, p2, int(half), color, -1, cv2.LINE_AA)


def _draw_torso(frame, l_shoulder, r_shoulder, l_hip, r_hip, color):
    if not all([l_shoulder, r_shoulder, l_hip, r_hip]):
        return
    pts = np.array([l_shoulder, r_shoulder, r_hip, l_hip], dtype=np.int32)
    cv2.fillConvexPoly(frame, pts, color, cv2.LINE_AA)


def _draw_head(frame, nose, color, scale):
    if not nose:
        return
    head_r = max(18, int(scale * 0.07))
    cv2.circle(frame, nose, head_r, color, -1, cv2.LINE_AA)


def _draw_hand(frame, wrist, elbow, color, scale):
    if not wrist or not elbow:
        return
    hand_r = max(7, int(scale * 0.025))
    cv2.circle(frame, wrist, hand_r, color, -1, cv2.LINE_AA)
    dx = wrist[0] - elbow[0]
    dy = wrist[1] - elbow[1]
    length = max(1, np.sqrt(dx**2 + dy**2))
    nx, ny = dx / length, dy / length
    px, py = -ny, nx
    finger_len = int(hand_r * 1.6)
    finger_w = max(2, hand_r // 3)
    for offset in [-0.9, -0.3, 0.3, 0.9]:
        fx = int(wrist[0] + px * offset * hand_r)
        fy = int(wrist[1] + py * offset * hand_r)
        tip_x = int(fx + nx * finger_len)
        tip_y = int(fy + ny * finger_len)
        _draw_capsule(frame, (fx, fy), (tip_x, tip_y), color, finger_w * 2)


def _draw_foot(frame, ankle, knee, color, scale):
    if not ankle or not knee:
        return
    foot_w = max(10, int(scale * 0.042))
    foot_h = max(6, int(scale * 0.022))
    dx = ankle[0] - knee[0]
    dy = ankle[1] - knee[1]
    length = max(1, np.sqrt(dx**2 + dy**2))
    nx, ny = dx / length, dy / length
    px, py = -ny, nx
    p1 = (int(ankle[0] - px * foot_w * 0.35), int(ankle[1] - py * foot_w * 0.35))
    p2 = (int(ankle[0] + px * foot_w * 0.75), int(ankle[1] + py * foot_w * 0.75))
    p3 = (int(p2[0] + nx * foot_h * 1.8), int(p2[1] + ny * foot_h * 1.8))
    p4 = (int(p1[0] + nx * foot_h * 1.8), int(p1[1] + ny * foot_h * 1.8))
    pts = np.array([p1, p2, p3, p4], dtype=np.int32)
    cv2.fillPoly(frame, [pts], color)
    cv2.polylines(
        frame, [pts], isClosed=True, color=color, thickness=1, lineType=cv2.LINE_AA
    )


class StickmanRenderer:
    """
    Renders segmented stickman fighters with dynamic auto-framing camera.
    - Zoomed out to show full scene
    - Auto-pans to keep all fighters centered
    - Smooth camera interpolation to avoid jarring jumps
    """

    def __init__(self, width: int, height: int, zoom: float = 0.55) -> None:
        self.width = width
        self.height = height
        self.scale = height
        self.zoom = zoom  # base zoom level — lower = further away

        # Smoothed camera state (interpolated each frame)
        self._smooth_ox: float = 0.0
        self._smooth_oy: float = 0.0
        self._smooth_zoom: float = zoom
        self._smoothing: float = 0.08  # 0=no smoothing, 1=instant snap

    def _apply_camera(
        self,
        landmarks: dict[int, dict],
        zoom: float,
        offset_x: float,
        offset_y: float,
    ) -> dict[int, dict]:
        """Scale landmarks toward center and apply pan offset."""
        cx, cy = self.width // 2, self.height // 2
        result = {}
        for idx, lm in landmarks.items():
            result[idx] = {
                "x": int(cx + (lm["x"] - cx) * zoom + offset_x),
                "y": int(cy + (lm["y"] - cy) * zoom + offset_y),
                "visibility": lm["visibility"],
            }
        return result

    def _compute_dynamic_camera(
        self,
        all_landmarks: list,
        padding: float = 0.3,
    ) -> tuple[float, float, float]:
        """
        Compute zoom + pan to keep all fighters centered and fully visible.
        Returns (zoom, offset_x, offset_y).
        """
        all_x, all_y = [], []
        for landmarks in all_landmarks:
            if not landmarks:
                continue
            for lm in landmarks.values():
                if lm["visibility"] >= VISIBILITY_THRESHOLD:
                    all_x.append(lm["x"])
                    all_y.append(lm["y"])

        if not all_x:
            return self.zoom, 0.0, 0.0

        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)

        # Center of all detected landmarks
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        # How much of the canvas the fighters currently span
        span_x = max_x - min_x
        span_y = max_y - min_y

        # Compute zoom so fighters fit within canvas with padding
        if span_x > 0 and span_y > 0:
            zoom_x = (self.width * (1.0 - padding)) / max(span_x, 1)
            zoom_y = (self.height * (1.0 - padding)) / max(span_y, 1)
            target_zoom = min(zoom_x, zoom_y, self.zoom)  # never zoom IN past base
        else:
            target_zoom = self.zoom

        # Pan offset to center the fighters
        cx, cy = self.width / 2, self.height / 2
        target_ox = cx - center_x * target_zoom
        target_oy = cy - center_y * target_zoom

        return target_zoom, target_ox, target_oy

    def _update_smooth_camera(
        self,
        target_zoom: float,
        target_ox: float,
        target_oy: float,
    ) -> tuple[float, float, float]:
        """
        Lerp current camera state toward target for smooth movement.
        Returns smoothed (zoom, offset_x, offset_y).
        """
        s = self._smoothing
        self._smooth_zoom += (target_zoom - self._smooth_zoom) * s
        self._smooth_ox += (target_ox - self._smooth_ox) * s
        self._smooth_oy += (target_oy - self._smooth_oy) * s
        return self._smooth_zoom, self._smooth_ox, self._smooth_oy

    def render_all(
        self,
        all_landmarks: list[dict[int, dict] | None],
    ) -> np.ndarray:
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:] = BG_COLOR

        # Compute where camera should be this frame
        target_zoom, target_ox, target_oy = self._compute_dynamic_camera(all_landmarks)

        # Smooth the camera movement
        zoom, ox, oy = self._update_smooth_camera(target_zoom, target_ox, target_oy)

        for fighter_idx, landmarks in enumerate(all_landmarks):
            if not landmarks:
                continue
            color = FIGHTER_COLORS[fighter_idx % len(FIGHTER_COLORS)]
            scaled = self._apply_camera(landmarks, zoom, ox, oy)
            self._draw_fighter(frame, scaled, color, fighter_idx + 1)

        return frame

    def _draw_fighter(
        self,
        frame: np.ndarray,
        landmarks: dict[int, dict],
        color: tuple,
        fighter_number: int,
    ) -> None:
        s = self.scale
        torso_t = max(10, int(s * 0.038))
        upper_t = max(9, int(s * 0.032))
        lower_t = max(8, int(s * 0.026))

        nose = _pt(landmarks, NOSE)
        l_shoulder = _pt(landmarks, LEFT_SHOULDER)
        r_shoulder = _pt(landmarks, RIGHT_SHOULDER)
        l_elbow = _pt(landmarks, LEFT_ELBOW)
        r_elbow = _pt(landmarks, RIGHT_ELBOW)
        l_wrist = _pt(landmarks, LEFT_WRIST)
        r_wrist = _pt(landmarks, RIGHT_WRIST)
        l_hip = _pt(landmarks, LEFT_HIP)
        r_hip = _pt(landmarks, RIGHT_HIP)
        l_knee = _pt(landmarks, LEFT_KNEE)
        r_knee = _pt(landmarks, RIGHT_KNEE)
        l_ankle = _pt(landmarks, LEFT_ANKLE)
        r_ankle = _pt(landmarks, RIGHT_ANKLE)
        mid_shoulder = _midpoint(l_shoulder, r_shoulder)

        # Draw order: back to front
        _draw_capsule(frame, l_hip, l_knee, color, upper_t)
        _draw_capsule(frame, l_knee, l_ankle, color, lower_t)
        _draw_capsule(frame, r_hip, r_knee, color, upper_t)
        _draw_capsule(frame, r_knee, r_ankle, color, lower_t)

        _draw_foot(frame, l_ankle, l_knee, color, s)
        _draw_foot(frame, r_ankle, r_knee, color, s)

        _draw_torso(frame, l_shoulder, r_shoulder, l_hip, r_hip, color)

        if mid_shoulder and nose:
            _draw_capsule(frame, mid_shoulder, nose, color, max(6, int(s * 0.022)))

        _draw_capsule(frame, l_shoulder, l_elbow, color, upper_t)
        _draw_capsule(frame, l_elbow, l_wrist, color, lower_t)
        _draw_capsule(frame, r_shoulder, r_elbow, color, upper_t)
        _draw_capsule(frame, r_elbow, r_wrist, color, lower_t)

        _draw_hand(frame, l_wrist, l_elbow, color, s)
        _draw_hand(frame, r_wrist, r_elbow, color, s)

        _draw_head(frame, nose, color, s)

        if nose:
            head_r = max(18, int(s * 0.07))
            label_pos = (nose[0] - 10, nose[1] - head_r - 10)
            cv2.putText(
                frame,
                f"P{fighter_number}",
                (label_pos[0] + 1, label_pos[1] + 1),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 0),
                3,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                f"P{fighter_number}",
                label_pos,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
                cv2.LINE_AA,
            )

    def render(self, landmarks: dict[int, dict]) -> np.ndarray:
        """Backward-compatible single-fighter render."""
        return self.render_all([landmarks])
