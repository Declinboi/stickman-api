# import cv2
# import numpy as np

# # ── Indices ─────────────────────────────────────
# NOSE = 0
# LEFT_SHOULDER = 11
# RIGHT_SHOULDER = 12
# LEFT_ELBOW = 13
# RIGHT_ELBOW = 14
# LEFT_WRIST = 15
# RIGHT_WRIST = 16
# LEFT_HIP = 23
# RIGHT_HIP = 24
# LEFT_KNEE = 25
# RIGHT_KNEE = 26
# LEFT_ANKLE = 27
# RIGHT_ANKLE = 28

# VISIBILITY_THRESHOLD = 0.1

# # FIXED: 3 colors for 3 fighters
# FIGHTER_COLORS = [
#     (255, 255, 255),  # Fighter 1 — white
#     (0, 255, 255),  # Fighter 2 — cyan
#     (0, 100, 255),  # Fighter 3 — orange
# ]

# # ── helpers ─────────────────────────────────────


# def _pt(lm, idx):
#     p = lm.get(idx)
#     if p and p["visibility"] >= VISIBILITY_THRESHOLD:
#         return (int(p["x"]), int(p["y"]))
#     return None


# def _mid(a, b):
#     if a and b:
#         return ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)
#     return a or b


# def _dist(a, b):
#     if not a or not b:
#         return 0
#     return np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


# # ── drawing ─────────────────────────────────────


# def draw_limb(frame, p1, p2, color, t):
#     if not p1 or not p2:
#         return
#     t = max(1, int(t))
#     cv2.line(frame, p1, p2, color, t, cv2.LINE_AA)
#     cv2.circle(frame, p1, max(1, t // 2), color, -1)
#     cv2.circle(frame, p2, max(1, t // 2), color, -1)


# def draw_joint(frame, p, r, color):
#     if p:
#         cv2.circle(frame, p, max(1, r), color, -1)


# def draw_head(frame, p, r, color):
#     if not p:
#         return
#     r = max(5, r)
#     cv2.circle(frame, p, r, color, -1)
#     cv2.circle(frame, (p[0] - r // 3, p[1] - r // 4), 2, (0, 0, 0), -1)
#     cv2.circle(frame, (p[0] + r // 3, p[1] - r // 4), 2, (0, 0, 0), -1)


# # ── effects ─────────────────────────────────────


# def motion_trail(frame, p1, p2, color, t):
#     for i in range(1, 4):
#         overlay = frame.copy()
#         alpha = 0.2 * (4 - i)
#         offset = i * 4
#         p1o = (p1[0] - offset, p1[1])
#         p2o = (p2[0] - offset, p2[1])
#         cv2.line(overlay, p1o, p2o, color, max(1, t), cv2.LINE_AA)
#         cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)


# def impact_effect(frame, p):
#     if not p:
#         return
#     for r in range(10, 40, 6):
#         cv2.circle(frame, p, r, (255, 255, 255), 1)


# def dynamic_thickness(p1, p2):
#     speed = _dist(p1, p2)
#     if speed == 0:
#         return 6
#     return int(max(5, min(18, speed * 0.05)))


# # ── background & floor ──────────────────────────


# def draw_background(frame, w, h):
#     top_color = np.array([40, 20, 10], dtype=np.float32)
#     bottom_color = np.array([80, 50, 20], dtype=np.float32)
#     for y in range(h):
#         t = y / h
#         color = ((1 - t) * top_color + t * bottom_color).astype(np.uint8)
#         frame[y, :] = color


# def draw_floor(frame, w, h):
#     floor_y = int(h * 0.88)
#     floor_color = (50, 80, 30)
#     line_color = (100, 160, 60)
#     shadow_color = (30, 50, 20)

#     cv2.rectangle(frame, (0, floor_y), (w, h), floor_color, -1)
#     cv2.line(frame, (0, floor_y), (w, floor_y), line_color, 3, cv2.LINE_AA)
#     cv2.line(frame, (0, floor_y - 1), (w, floor_y - 1), shadow_color, 1, cv2.LINE_AA)


# # ── renderer ────────────────────────────────────


# class StickmanRenderer:
#     def __init__(self, w, h, num_fighters=3):  # FIXED: num_fighters param
#         self.w = w
#         self.h = h
#         # FIXED: dynamically sized to num_fighters instead of hardcoded 2
#         self.prev = [None] * num_fighters
#         self.last_known = [None] * num_fighters

#     def render_all(self, all_landmarks):
#         frame = np.zeros((self.h, self.w, 3), dtype=np.uint8)
#         draw_background(frame, self.w, self.h)
#         draw_floor(frame, self.w, self.h)

#         impact_detected = False

#         # FIXED: dynamically grow internal state if more fighters appear
#         if len(all_landmarks) > len(self.prev):
#             extra = len(all_landmarks) - len(self.prev)
#             self.prev += [None] * extra
#             self.last_known += [None] * extra

#         for i, lm in enumerate(all_landmarks):
#             if lm:
#                 self.last_known[i] = lm
#             else:
#                 lm = self.last_known[i]

#             if not lm:
#                 continue

#             color = FIGHTER_COLORS[i % len(FIGHTER_COLORS)]
#             impact = self.draw_fighter(frame, lm, color, i)

#             if impact:
#                 impact_detected = True

#         # FIXED: check impacts across ALL fighter pairs, not just 0 vs 1
#         self._check_cross_impacts(frame, all_landmarks)

#         return frame, impact_detected

#     def _check_cross_impacts(self, frame, all_landmarks):
#         """Check wrist proximity between every pair of fighters."""
#         lms = [
#             self.last_known[i] if not all_landmarks[i] else all_landmarks[i]
#             for i in range(len(all_landmarks))
#         ]
#         for i in range(len(lms)):
#             for j in range(i + 1, len(lms)):
#                 if not lms[i] or not lms[j]:
#                     continue
#                 # Check if any wrist of fighter i is close to any wrist of fighter j
#                 for wi in [LEFT_WRIST, RIGHT_WRIST]:
#                     for wj in [LEFT_WRIST, RIGHT_WRIST]:
#                         pi = _pt(lms[i], wi)
#                         pj = _pt(lms[j], wj)
#                         if pi and pj and _dist(pi, pj) < 40:
#                             impact_effect(frame, _mid(pi, pj))

#     def draw_fighter(self, frame, lm, color, idx):
#         prev = self.prev[idx]

#         l_sh = _pt(lm, LEFT_SHOULDER)
#         r_sh = _pt(lm, RIGHT_SHOULDER)
#         l_el = _pt(lm, LEFT_ELBOW)
#         r_el = _pt(lm, RIGHT_ELBOW)
#         l_wr = _pt(lm, LEFT_WRIST)
#         r_wr = _pt(lm, RIGHT_WRIST)
#         l_hp = _pt(lm, LEFT_HIP)
#         r_hp = _pt(lm, RIGHT_HIP)
#         l_kn = _pt(lm, LEFT_KNEE)
#         r_kn = _pt(lm, RIGHT_KNEE)
#         l_an = _pt(lm, LEFT_ANKLE)
#         r_an = _pt(lm, RIGHT_ANKLE)
#         nose = _pt(lm, NOSE)

#         mid_sh = _mid(l_sh, r_sh)
#         mid_hp = _mid(l_hp, r_hp)

#         sh_width = _dist(l_sh, r_sh) if (l_sh and r_sh) else 40
#         head_r = max(12, int(sh_width * 0.35))

#         # ── Head position ─────────────────────────────
#         if nose:
#             head_pt = nose
#         elif mid_sh:
#             head_pt = (mid_sh[0], mid_sh[1] - int(sh_width * 0.6))
#         else:
#             head_pt = None

#         t_arm = dynamic_thickness(l_sh, l_el)
#         t_leg = dynamic_thickness(l_hp, l_kn)

#         # ── Neck ─────────────────────────────────────
#         if head_pt and mid_sh:
#             dist_nh = max(_dist(head_pt, mid_sh), 1)
#             dx = mid_sh[0] - head_pt[0]
#             dy = mid_sh[1] - head_pt[1]
#             neck_top = (
#                 int(head_pt[0] + (dx / dist_nh) * head_r),
#                 int(head_pt[1] + (dy / dist_nh) * head_r),
#             )
#             cv2.line(frame, neck_top, mid_sh, color, 5, cv2.LINE_AA)

#         # ── Shoulder & Hip bars ───────────────────────
#         draw_limb(frame, l_sh, r_sh, color, 6)
#         draw_limb(frame, l_hp, r_hp, color, 6)

#         # ── Arms ──────────────────────────────────────
#         draw_limb(frame, l_sh, l_el, color, t_arm)
#         draw_limb(frame, l_el, l_wr, color, t_arm)
#         draw_limb(frame, r_sh, r_el, color, t_arm)
#         draw_limb(frame, r_el, r_wr, color, t_arm)

#         # ── Legs ──────────────────────────────────────
#         draw_limb(frame, l_hp, l_kn, color, t_leg)
#         draw_limb(frame, l_kn, l_an, color, t_leg)
#         draw_limb(frame, r_hp, r_kn, color, t_leg)
#         draw_limb(frame, r_kn, r_an, color, t_leg)

#         # ── Torso ─────────────────────────────────────
#         draw_limb(frame, mid_sh, mid_hp, color, 8)

#         # ── Head (on top of everything) ───────────────
#         draw_head(frame, head_pt, head_r, color)

#         # ── Motion trails ────────────────────────────
#         if prev:
#             p_prev = _pt(prev, LEFT_WRIST)
#             if p_prev and l_wr and _dist(p_prev, l_wr) > 20:
#                 motion_trail(frame, p_prev, l_wr, color, t_arm)

#         # ── Impact detection (self — both wrists close) ──
#         impact = False
#         if l_wr and r_wr and _dist(l_wr, r_wr) < 40:
#             impact_effect(frame, _mid(l_wr, r_wr))
#             impact = True

#         self.prev[idx] = lm
#         return impact
