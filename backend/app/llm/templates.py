"""
llm/templates.py — Deterministic fallback templates.

Per Section 8.4 of the specification:
At least 12 templates (4 styles x 3 levels) + 3 dedicated templates for counts_start_number.
All templates:
- Must never mention or reveal the correct answer
- Must have at most 25 words
- Must have at most 2 sentences
- Must have at most 1 question mark
- Must pass all validators in validators.py
"""
from __future__ import annotations

TEMPLATES: dict[tuple[str, int], str] = {
    # ── Story Style ────────────────────────────────────────────────────────────
    ("story", 1): "We need more {noun} for our journey. How many do we add?",
    ("story", 2): "Picture {a} {noun} ready, then load {b} more. What do you see?",
    ("story", 3): "With {par_a} {noun} plus {par_b} we got {par_ans}. What about {a} plus {b}?",

    # ── Visual Style ───────────────────────────────────────────────────────────
    ("visual", 1): "Look at the {noun} on screen. What happens if we count on?",
    ("visual", 2): "Touch {a} {noun} first, then count {b} more. How many in all?",
    ("visual", 3): "Seeing {par_a} and {par_b} gave {par_ans}. Now count {a} and {b}.",

    # ── Question Style ─────────────────────────────────────────────────────────
    ("question", 1): "You have {a} {noun} and get {b} more. What is the total?",
    ("question", 2): "Start at {a} and jump forward {b} steps. Where do you land?",
    ("question", 3): "Since {par_a} plus {par_b} makes {par_ans}, what about {a} plus {b}?",

    # ── Physical Style ─────────────────────────────────────────────────────────
    ("physical", 1): "Tap your fingers {b} times past {a}. What number comes up?",
    ("physical", 2): "Hold up {a} fingers, then raise {b} more. How many fingers now?",
    ("physical", 3): "Tapping {par_a} then {par_b} gave {par_ans}. Try tapping {a} and {b}.",
}

# Specialized templates for counts_start_number misconception
MISCONCEPTION_TEMPLATES: dict[tuple[str, int], str] = {
    ("counts_start_number", 1): "Remember, start counting after {a}. What is the next number?",
    ("counts_start_number", 2): "Put {a} in your pocket and step {b} forward. Where are you?",
    ("counts_start_number", 3): "For {par_a} and {par_b} we started past {par_a} to reach {par_ans}. Try {a} and {b}!",
}


def render_template(
    style: str,
    level: int,
    misconception_id: str = "",
    name: str = "Friend",
    noun: str = "stars",
    a: int = 3,
    b: int = 4,
    par_a: int = 2,
    par_b: int = 3,
    par_ans: int = 5,
) -> str:
    """
    Renders the appropriate template with the given context placeholders.
    """
    # Check misconception-specific template first
    if misconception_id == "counts_start_number":
        tmpl = MISCONCEPTION_TEMPLATES.get((misconception_id, level))
        if tmpl:
            return tmpl.format(
                name=name, noun=noun, a=a, b=b,
                par_a=par_a, par_b=par_b, par_ans=par_ans,
            )

    # Standard (style, level) template
    tmpl = TEMPLATES.get((style, level))
    if not tmpl:
        tmpl = TEMPLATES.get(("story", 1), "How many {noun} do we have in all?")

    return tmpl.format(
        name=name, noun=noun, a=a, b=b,
        par_a=par_a, par_b=par_b, par_ans=par_ans,
    )
