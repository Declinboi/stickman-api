import numpy as np


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation."""
    return a + (b - a) * t


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def ease_in_out(t: float) -> float:
    """Smooth S-curve — slow start, fast middle, slow end."""
    t = clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def ease_in(t: float) -> float:
    """Accelerating from rest."""
    t = clamp(t, 0.0, 1.0)
    return t * t


def ease_out(t: float) -> float:
    """Decelerating to rest."""
    t = clamp(t, 0.0, 1.0)
    return 1.0 - (1.0 - t) ** 2


def anticipation_curve(t: float, anticipation: float = 0.12) -> float:
    """
    Classic animation anticipation — slight pull-back before the main motion.
    t in [0, anticipation]: pull back (negative)
    t in [anticipation, 1]: main motion
    """
    t = clamp(t, 0.0, 1.0)
    if t < anticipation:
        return -ease_in(t / anticipation) * 0.25
    return ease_out((t - anticipation) / (1.0 - anticipation))


def overshoot_curve(t: float, overshoot: float = 0.15) -> float:
    """
    Motion that overshoots the target then settles back.
    """
    t = clamp(t, 0.0, 1.0)
    if t < (1.0 - overshoot):
        return ease_in_out(t / (1.0 - overshoot))
    settle_t = (t - (1.0 - overshoot)) / overshoot
    return 1.0 + (1.0 - ease_out(settle_t)) * 0.15


def spring(t: float, frequency: float = 12.0, decay: float = 6.0) -> float:
    """Damped spring — oscillates then settles at 1.0."""
    t = clamp(t, 0.0, 1.0)
    return 1.0 - np.exp(-decay * t) * np.cos(frequency * t)


def punch_curve(t: float) -> float:
    """
    Fast snap out, instant return — classic punch motion shape.
    Phase 0→0.35: anticipation wind-up
    Phase 0.35→0.55: explosive extension
    Phase 0.55→1.0: recovery pull back
    """
    t = clamp(t, 0.0, 1.0)
    if t < 0.35:
        return -ease_in(t / 0.35) * 0.18  # wind-up
    elif t < 0.55:
        return ease_out((t - 0.35) / 0.20)  # strike
    else:
        return 1.0 - ease_in_out((t - 0.55) / 0.45)  # recovery


def kick_curve(t: float) -> float:
    """
    Chamber → extend → retract.
    Phase 0→0.30: chambering (knee up)
    Phase 0.30→0.58: extension
    Phase 0.58→1.00: retract and land
    """
    t = clamp(t, 0.0, 1.0)
    if t < 0.30:
        return ease_in(t / 0.30) * 0.5  # chamber
    elif t < 0.58:
        return 0.5 + ease_out((t - 0.30) / 0.28) * 0.5  # extend
    else:
        return 1.0 - ease_in_out((t - 0.58) / 0.42)  # retract


def block_curve(t: float) -> float:
    """Snap up to guard, hold, slowly lower."""
    t = clamp(t, 0.0, 1.0)
    if t < 0.20:
        return ease_out(t / 0.20)
    elif t < 0.75:
        return 1.0
    else:
        return 1.0 - ease_in_out((t - 0.75) / 0.25) * 0.6


def knockback_curve(t: float) -> float:
    """Sudden jolt back then stagger forward."""
    t = clamp(t, 0.0, 1.0)
    if t < 0.25:
        return ease_out(t / 0.25)
    else:
        return 1.0 - ease_in_out((t - 0.25) / 0.75) * 0.7


def idle_breathe(t: float, speed: float = 1.0) -> float:
    """Gentle sine-wave breathing cycle for idle stance."""
    return np.sin(t * speed * np.pi * 2) * 0.5 + 0.5
