import cv2
import numpy as np
from pose_generator import Pose
from motion_curves import clamp

FIGHTER_COLORS = [
    (255, 255, 255),  # P1 — white
    (0, 255, 255),  # P2 — yellow
]

SKY_TOP = (30, 18, 12)
SKY_BOT = (70, 45, 28)
FLOOR_COL = (12, 8, 5)
FLOOR_GRID = (28, 18, 10)
FLOOR_Y = 0.72

_SPEC = (220, 220, 255)
_DARK = 0.40
_MID = 0.70


def _dk(c, f):
    return tuple(max(0, min(255, int(x * f))) for x in c)


def _bl(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_background(frame, w, h):
    fy = int(h * FLOOR_Y)
    for y in range(fy):
        t = y / max(fy - 1, 1)
        cv2.line(frame, (0, y), (w, y), _bl(SKY_TOP, SKY_BOT, t), 1)
    cv2.rectangle(frame, (0, fy), (w, h), FLOOR_COL, -1)
    gw = int(h * 0.035)
    for i in range(gw):
        a = 1.0 - i / gw
        cv2.line(
            frame, (0, fy + i), (w, fy + i), _bl(FLOOR_COL, (90, 58, 30), a * 0.55), 1
        )
    cx = w // 2
    sp = w * 1.1
    for i in range(13):
        t = i / 12
        bx = int(-sp / 2 + t * sp)
        cv2.line(frame, (cx + (bx - cx) // 7, fy), (bx, h), FLOOR_GRID, 1, cv2.LINE_AA)
    for i in range(1, 9):
        t = (i / 8) ** 1.7
        y = int(fy + t * (h - fy))
        xi = int((1.0 - t) * w * 0.42)
        cv2.line(frame, (xi, y), (w - xi, y), FLOOR_GRID, 1, cv2.LINE_AA)


def draw_shadow(frame, pose: Pose, floor_y: int):
    mx = int((pose.l_ankle[0] + pose.r_ankle[0]) / 2)
    my = min(floor_y + 10, frame.shape[0] - 4)
    sw = max(22, int(abs(pose.l_ankle[0] - pose.r_ankle[0]) * 1.4))
    sh = max(7, sw // 4)
    for layer in range(4):
        sc = 1.0 + layer * 0.3
        al = 0.18 - layer * 0.04
        ov = frame.copy()
        cv2.ellipse(
            ov,
            (mx, my),
            (int(sw * sc), int(sh * sc)),
            0,
            0,
            360,
            (0, 0, 0),
            -1,
            cv2.LINE_AA,
        )
        cv2.addWeighted(ov, al, frame, 1 - al, 0, frame)


def draw_cylinder(frame, p1, p2, color, thickness):
    if not p1 or not p2:
        return
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    ln = max(1.0, float(np.sqrt(dx**2 + dy**2)))
    px = -dy / ln
    py = dx / ln
    h = thickness / 2.0
    bands = [
        (-1.00, -0.55, _dk(color, _DARK)),
        (-0.55, -0.10, _dk(color, _MID)),
        (-0.10, 0.40, color),
        (0.40, 0.75, _dk(color, _MID)),
        (0.75, 1.00, _dk(color, _DARK)),
    ]
    for ts, te, bc in bands:
        c1 = (int(p1[0] + px * ts * h), int(p1[1] + py * ts * h))
        c2 = (int(p1[0] + px * te * h), int(p1[1] + py * te * h))
        c3 = (int(p2[0] + px * te * h), int(p2[1] + py * te * h))
        c4 = (int(p2[0] + px * ts * h), int(p2[1] + py * ts * h))
        cv2.fillConvexPoly(frame, np.array([c1, c2, c3, c4], np.int32), bc, cv2.LINE_AA)
    so = 0.25
    sp1 = (int(p1[0] + px * so * h), int(p1[1] + py * so * h))
    sp2 = (int(p2[0] + px * so * h), int(p2[1] + py * so * h))
    cv2.line(frame, sp1, sp2, _SPEC, max(1, thickness // 6), cv2.LINE_AA)
    cv2.circle(frame, p1, int(h), _dk(color, _MID), -1, cv2.LINE_AA)
    cv2.circle(frame, p2, int(h), _dk(color, _MID), -1, cv2.LINE_AA)


def draw_sphere(frame, center, radius, color):
    if not center:
        return
    cx, cy = int(center[0]), int(center[1])
    cv2.circle(frame, (cx, cy), radius, _dk(color, _DARK), -1, cv2.LINE_AA)
    cv2.circle(frame, (cx, cy), int(radius * 0.82), _dk(color, _MID), -1, cv2.LINE_AA)
    lox = -int(radius * 0.22)
    loy = -int(radius * 0.22)
    cv2.circle(frame, (cx + lox, cy + loy), int(radius * 0.58), color, -1, cv2.LINE_AA)
    cv2.circle(
        frame,
        (cx - int(radius * 0.3), cy - int(radius * 0.3)),
        max(2, int(radius * 0.2)),
        _SPEC,
        -1,
        cv2.LINE_AA,
    )


def draw_torso(frame, ls, rs, lh, rh, color):
    if not all([ls, rs, lh, rh]):
        return
    pts = np.array([ls, rs, rh, lh], np.int32)
    cv2.fillConvexPoly(frame, pts, _dk(color, _MID), cv2.LINE_AA)
    ms = ((ls[0] + rs[0]) // 2, (ls[1] + rs[1]) // 2)
    mh = ((lh[0] + rh[0]) // 2, (lh[1] + rh[1]) // 2)
    if ms and mh:
        lb = np.array([ls, ms, mh, lh], np.int32)
        ov = frame.copy()
        cv2.fillConvexPoly(ov, lb, _dk(color, _DARK), cv2.LINE_AA)
        cv2.addWeighted(ov, 0.42, frame, 0.58, 0, frame)
        rb = np.array([ms, rs, rh, mh], np.int32)
        ov2 = frame.copy()
        cv2.fillConvexPoly(ov2, rb, color, cv2.LINE_AA)
        cv2.addWeighted(ov2, 0.32, frame, 0.68, 0, frame)
        cv2.line(frame, ms, mh, _SPEC, 1, cv2.LINE_AA)


def draw_foot(frame, ankle, knee, color, scale):
    if not ankle or not knee:
        return
    fw = max(14, int(scale * 0.046))
    fh = max(8, int(scale * 0.025))
    dx = ankle[0] - knee[0]
    dy = ankle[1] - knee[1]
    ln = max(1.0, float(np.sqrt(dx**2 + dy**2)))
    nx = dx / ln
    ny = dy / ln
    px = -ny
    py = nx
    p1 = (int(ankle[0] - px * fw * 0.35), int(ankle[1] - py * fw * 0.35))
    p2 = (int(ankle[0] + px * fw * 0.78), int(ankle[1] + py * fw * 0.78))
    p3 = (int(p2[0] + nx * fh * 2.0), int(p2[1] + ny * fh * 2.0))
    p4 = (int(p1[0] + nx * fh * 2.0), int(p1[1] + ny * fh * 2.0))
    tp = np.array([p1, p2, p3, p4], np.int32)
    sp = np.array(
        [p2, p3, (p3[0], p3[1] + fh // 2), (p2[0], p2[1] + fh // 2)], np.int32
    )
    cv2.fillPoly(frame, [tp], _dk(color, _MID), cv2.LINE_AA)
    cv2.fillPoly(frame, [sp], _dk(color, _DARK), cv2.LINE_AA)
    cv2.polylines(frame, [tp], True, _dk(color, _DARK), 1, cv2.LINE_AA)


def draw_hand(frame, wrist, elbow, color, scale):
    if not wrist or not elbow:
        return
    hr = max(9, int(scale * 0.030))
    draw_sphere(frame, wrist, hr, color)
    dx = wrist[0] - elbow[0]
    dy = wrist[1] - elbow[1]
    ln = max(1.0, float(np.sqrt(dx**2 + dy**2)))
    nx = dx / ln
    ny = dy / ln
    px = -ny
    py = nx
    fl = int(hr * 1.5)
    ft = max(4, hr // 3)
    for off in [-0.9, -0.3, 0.3, 0.9]:
        fx = int(wrist[0] + px * off * hr)
        fy = int(wrist[1] + py * off * hr)
        tip = (int(fx + nx * fl), int(fy + ny * fl))
        draw_cylinder(frame, (fx, fy), tip, color, ft * 2)


def draw_trail(frame, trail: list, color: tuple):
    for i, (tx, ty) in enumerate(trail[:-1]):
        alpha = (i / len(trail)) * 0.35
        radius = max(2, int(6 * (i / len(trail))))
        ov = frame.copy()
        cv2.circle(ov, (int(tx), int(ty)), radius, color, -1, cv2.LINE_AA)
        cv2.addWeighted(ov, alpha, frame, 1 - alpha, 0, frame)


# draw_hud intentionally removed — no health bars


def draw_fighter(
    frame, pose: Pose, color: tuple, scale: int, fighter_number: int, hit_flash: int = 0
):
    draw_color = (255, 255, 255) if hit_flash > 0 else color

    s = scale
    ut = max(10, int(s * 0.036))
    lt = max(8, int(s * 0.028))
    nt = max(6, int(s * 0.022))
    jr = max(7, int(s * 0.024))
    hr = max(20, int(s * 0.065))

    def ip(pt):
        return (int(pt[0]), int(pt[1]))

    draw_cylinder(frame, ip(pose.l_hip), ip(pose.l_knee), draw_color, ut)
    draw_cylinder(frame, ip(pose.r_hip), ip(pose.r_knee), draw_color, ut)
    draw_cylinder(frame, ip(pose.l_knee), ip(pose.l_ankle), draw_color, lt)
    draw_cylinder(frame, ip(pose.r_knee), ip(pose.r_ankle), draw_color, lt)
    draw_sphere(frame, ip(pose.l_knee), jr, draw_color)
    draw_sphere(frame, ip(pose.r_knee), jr, draw_color)
    draw_foot(frame, ip(pose.l_ankle), ip(pose.l_knee), draw_color, s)
    draw_foot(frame, ip(pose.r_ankle), ip(pose.r_knee), draw_color, s)
    draw_sphere(frame, ip(pose.l_ankle), jr - 1, draw_color)
    draw_sphere(frame, ip(pose.r_ankle), jr - 1, draw_color)
    draw_torso(
        frame,
        ip(pose.l_shoulder),
        ip(pose.r_shoulder),
        ip(pose.l_hip),
        ip(pose.r_hip),
        draw_color,
    )
    draw_sphere(frame, ip(pose.l_shoulder), jr, draw_color)
    draw_sphere(frame, ip(pose.r_shoulder), jr, draw_color)
    draw_sphere(frame, ip(pose.l_hip), jr - 1, draw_color)
    draw_sphere(frame, ip(pose.r_hip), jr - 1, draw_color)
    draw_cylinder(frame, ip(pose.neck), ip(pose.head), draw_color, nt)
    draw_cylinder(frame, ip(pose.l_shoulder), ip(pose.l_elbow), draw_color, ut)
    draw_cylinder(frame, ip(pose.r_shoulder), ip(pose.r_elbow), draw_color, ut)
    draw_cylinder(frame, ip(pose.l_elbow), ip(pose.l_wrist), draw_color, lt)
    draw_cylinder(frame, ip(pose.r_elbow), ip(pose.r_wrist), draw_color, lt)
    draw_sphere(frame, ip(pose.l_elbow), jr, draw_color)
    draw_sphere(frame, ip(pose.r_elbow), jr, draw_color)
    draw_hand(frame, ip(pose.l_wrist), ip(pose.l_elbow), draw_color, s)
    draw_hand(frame, ip(pose.r_wrist), ip(pose.r_elbow), draw_color, s)
    draw_sphere(frame, ip(pose.head), hr, draw_color)
