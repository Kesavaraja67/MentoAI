"""
engines/mastery.py — Explainable mastery confidence updates.

Per Section 7.3 of the specification:
Applied to the skill of the problem in the session graph after every attempt.
- correct at hint level h: c = c + (1 - c) * gain[h]
    gain = [0.35, 0.18, 0.10, 0.05] for h = 0, 1, 2, 3
- wrong: c = c - c * 0.20
- clamp to [0.0, 1.0]

Thresholds:
- weak: < 0.5
- mastered: >= 0.8
"""
from __future__ import annotations

GAIN = [0.35, 0.18, 0.10, 0.05]
WEAK_THRESHOLD = 0.5
MASTERED_THRESHOLD = 0.8


def update_confidence(
    current: float,
    correct: bool,
    hint_level: int = 0,
) -> float:
    """
    Computes updated confidence after an attempt.
    """
    c = float(current)

    if correct:
        # Clamp hint level to valid index in gain table
        h = max(0, min(hint_level, len(GAIN) - 1))
        c = c + (1.0 - c) * GAIN[h]
    else:
        c = c - c * 0.20

    # Clamp to [0.0, 1.0] and round to 4 decimals for precision & readability
    clamped = max(0.0, min(1.0, c))
    return round(clamped, 4)


def is_weak(confidence: float) -> bool:
    """True if confidence is strictly below 0.5."""
    return confidence < WEAK_THRESHOLD


def is_mastered(confidence: float) -> bool:
    """True if confidence is 0.8 or higher."""
    return confidence >= MASTERED_THRESHOLD
