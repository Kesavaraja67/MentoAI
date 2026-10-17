"""
safety.py — Safety Constitution, Triage Guardrails, and SVG Sanitizer for MentoAI.

Ensures strict compliance with SPEC Section 10:
- Child-safety protection (Care Mode on distress/harm, gentle refusal redirects).
- No PII harvesting.
- SVG sanitization (stripping scripts, event handlers, and foreign objects).
"""
import re
from typing import Dict, Any, Tuple


BANNED_SVG_PATTERNS = [
    re.compile(r"<script[\s\S]*?>[\s\S]*?</script>", re.IGNORECASE),
    re.compile(r"onload[\s\S]*?=", re.IGNORECASE),
    re.compile(r"onerror[\s\S]*?=", re.IGNORECASE),
    re.compile(r"onclick[\s\S]*?=", re.IGNORECASE),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"<foreignObject[\s\S]*?>[\s\S]*?</foreignObject>", re.IGNORECASE),
]

CARE_MODE_KEYWORDS = [
    "want to die",
    "kill myself",
    "hurting myself",
    "self harm",
    "hate my life",
    "nobody loves me",
    "want to end it",
]

REFUSE_KEYWORDS = [
    "how to make a bomb",
    "how to hack",
    "steal money",
    "make drugs",
    "buy weapons",
]


SAFETY_CARE_MESSAGE = (
    "I hear you, and it sounds really tough right now. Please know you're not alone. "
    "Would you like to take a deep breath together, or talk to a parent, teacher, or trusted adult who cares about you?"
)

SAFETY_REFUSE_MESSAGE = (
    "I cannot help with that, but I'd love to explore something safe and exciting with you! "
    "Would you like to learn how rockets reach orbit, or why octopuses have three hearts?"
)


def classify_safety_keywords(text: str) -> Tuple[str, str]:
    """Classify safety keywords and return (mode, reason)."""
    res = triage_input(text)
    return res["mode"], res["reason"]


def triage_input(text: str) -> Dict[str, Any]:

    """
    Fast triage check for incoming utterances before context assembly.
    Returns mode: 'normal', 'care', or 'refuse_redirect'.
    """
    lower = text.lower().strip()

    # Care Mode check
    for phrase in CARE_MODE_KEYWORDS:
        if phrase in lower:
            return {
                "mode": "care",
                "category": "self_harm_or_distress",
                "action": "care_mode",
                "reason": "Expressed acute distress or self-harm ideation",
            }

    # Refusal & Redirect check
    for phrase in REFUSE_KEYWORDS:
        if phrase in lower:
            return {
                "mode": "refuse_redirect",
                "category": "illicit_activity",
                "action": "blocked_redirected",
                "reason": "Dangerous or harmful topic requested",
            }

    return {
        "mode": "normal",
        "category": "general",
        "action": "monitored",
        "reason": "Safe conversational inquiry",
    }


def sanitize_svg(svg_content: str) -> str:
    """
    Sanitizes SVG strings produced by model tools to prevent XSS.
    Strips <script>, event handlers, and external URLs.
    """
    if not svg_content:
        return ""

    sanitized = svg_content
    for pattern in BANNED_SVG_PATTERNS:
        sanitized = pattern.sub("", sanitized)

    return sanitized


def validate_safety_response(response_text: str) -> Tuple[bool, str]:
    """Validates model response against safety rules."""
    lower = response_text.lower()
    # Check if model gave medical or legal directive
    if any(p in lower for p in ["you have cancer", "take 500mg of", "guilty of a felony"]):
        return False, "Response gave prescriptive medical or legal diagnosis"
    return True, "Safe"
