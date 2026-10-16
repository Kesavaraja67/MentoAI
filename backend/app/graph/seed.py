"""
graph/seed.py — Curriculum skills, misconceptions, and synthetic personas.

This is the single source of truth for all static data.
The curriculum is defined as Python data, then written to the `curriculum`
FalkorDB graph on first seed (and on demo reset).

Section 6.1 and 6.2 of the spec define all values here.
"""
from __future__ import annotations

# ── Curriculum: 13 skills ────────────────────────────────────────────────────
# Each entry: (id, name, order, prerequisites: list[id])
SKILLS: list[dict] = [
    {"id": "count_10",      "name": "Counting to 10",       "order": 1,  "prereqs": []},
    {"id": "count_20",      "name": "Counting to 20",       "order": 2,  "prereqs": ["count_10"]},
    {"id": "one_more_less", "name": "One more, one less",   "order": 3,  "prereqs": ["count_20"]},
    {"id": "bonds_5",       "name": "Number bonds to 5",    "order": 4,  "prereqs": ["count_10"]},
    {"id": "count_on",      "name": "Counting on",          "order": 5,  "prereqs": ["count_20", "one_more_less"]},
    {"id": "add_5",         "name": "Addition within 5",    "order": 6,  "prereqs": ["bonds_5", "count_on"]},
    {"id": "sub_5",         "name": "Subtraction within 5", "order": 7,  "prereqs": ["add_5"]},
    {"id": "bonds_10",      "name": "Number bonds to 10",   "order": 8,  "prereqs": ["bonds_5", "count_20"]},
    {"id": "add_10",        "name": "Addition within 10",   "order": 9,  "prereqs": ["add_5", "bonds_10"]},
    {"id": "sub_10",        "name": "Subtraction within 10","order": 10, "prereqs": ["sub_5", "add_10"]},
    {"id": "doubles",       "name": "Doubles",              "order": 11, "prereqs": ["add_10"]},
    {"id": "make_ten",      "name": "Making ten",           "order": 12, "prereqs": ["bonds_10", "add_10"]},
    {"id": "add_20",        "name": "Addition within 20",   "order": 13, "prereqs": ["make_ten", "doubles"]},
]

# ── Misconceptions (spec section 6.2) ────────────────────────────────────────
# Each entry: (id, name, indicates_weak_skill_id)
MISCONCEPTIONS: list[dict] = [
    {
        "id": "counts_start_number",
        "name": "Counts the starting number as one of the steps",
        "indicates": "count_on",
    },
    {
        "id": "overshoots_by_one",
        "name": "Counts one too many",
        "indicates": "one_more_less",
    },
    {
        "id": "adds_instead_of_subtracts",
        "name": "Adds when asked to take away",
        "indicates": "sub_5",
    },
    {
        "id": "subtracts_instead_of_adds",
        "name": "Takes away when asked to put together",
        "indicates": "add_5",
    },
    {
        "id": "reports_an_addend",
        "name": "Answers with one of the numbers given",
        "indicates": "bonds_5",
    },
]

# ── HintStyle defaults (spec section 6.3) ────────────────────────────────────
# Default order: story, visual, question, physical. Default score 0.5, tries 0.
HINT_STYLES: list[dict] = [
    {"id": "story",    "order": 1, "score": 0.5, "tries": 0},
    {"id": "visual",   "order": 2, "score": 0.5, "tries": 0},
    {"id": "question", "order": 3, "score": 0.5, "tries": 0},
    {"id": "physical", "order": 4, "score": 0.5, "tries": 0},
]

# ── Synthetic personas (spec section 6.4) ────────────────────────────────────
PERSONAS: list[dict] = [
    {
        "id": "leo",
        "name": "Leo",
        "age": 6,
        "interests": ["space", "rockets"],
        "object_set": "space",
        "opening_problem": {"skill_id": "count_on", "op": "+", "a": 3, "b": 4},
        "confidences": {
            "count_10":      0.95,
            "count_20":      0.90,
            "one_more_less": 0.85,
            "bonds_5":       0.85,
            "count_on":      0.35,
            "add_5":         0.60,
            # rest default to 0.0
        },
    },
    {
        "id": "meera",
        "name": "Meera",
        "age": 5,
        "interests": ["dinosaurs"],
        "object_set": "dinosaur",
        "opening_problem": None,
        "confidences": {
            "count_10": 0.70,
            "count_20": 0.30,
            # rest default to 0.0
        },
    },
    {
        "id": "arjun",
        "name": "Arjun",
        "age": 7,
        "interests": ["cricket"],
        "object_set": "cricket",
        "opening_problem": None,
        "confidences": {
            "count_10":      0.90,
            "count_20":      0.90,
            "one_more_less": 0.90,
            "bonds_5":       0.85,
            "count_on":      0.90,
            "add_5":         0.90,
            "sub_5":         0.85,
            "bonds_10":      0.85,
            "add_10":        0.85,
            "sub_10":        0.45,
            "doubles":       0.30,
            # rest default to 0.0
        },
    },
]

# ── Helper: default confidence for a skill not listed ────────────────────────
def get_confidence(persona: dict, skill_id: str) -> float:
    return persona["confidences"].get(skill_id, 0.0)
