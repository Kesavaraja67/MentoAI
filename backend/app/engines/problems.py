"""
engines/problems.py — Deterministic problem generator.

Seeded by (child_id, session_index, turn_n) so identical inputs produce
identical problems across restarts. Supports all 13 curriculum skills.
Generates parallel problems for Level 3 worked examples with the guarantee
that no operand and no result equals the original answer.
"""
from __future__ import annotations

import random
from typing import Any
from app.graph.seed import PERSONAS


def _get_persona(child_id: str) -> dict | None:
    for p in PERSONAS:
        if p["id"] == child_id:
            return p
    return None


def _get_seed_rng(child_id: str, session_index: int, turn_n: int, salt: int = 0) -> random.Random:
    seed_str = f"{child_id}:{session_index}:{turn_n}:{salt}"
    return random.Random(seed_str)


def generate_problem(
    child_id: str,
    skill_id: str,
    session_index: int = 1,
    turn_n: int = 0,
    easier: bool = False,
    salt: int = 0,
) -> dict[str, Any]:
    """
    Generate a math problem for the given skill, deterministically seeded.
    If turn_n == 0 and the persona defines an opening_problem matching skill_id,
    that problem is used.
    """
    persona = _get_persona(child_id)
    object_set = persona["object_set"] if persona else "space"

    # Check for persona's scripted opening problem
    if turn_n == 0 and salt == 0 and persona and persona.get("opening_problem"):
        op_prob = persona["opening_problem"]
        if op_prob.get("skill_id") == skill_id:
            op = op_prob["op"]
            a = op_prob["a"]
            b = op_prob["b"]
            ans = a + b if op == "+" else (a - b if op == "-" else 5 - a)
            prob_id = f"prob_{child_id}_{session_index}_{turn_n}_{skill_id}_scripted"
            return {
                "problem_id": prob_id,
                "skill_id": skill_id,
                "op": op,
                "a": a,
                "b": b,
                "answer": ans,
                "story_slots": {
                    "object_set": object_set,
                    "a": a,
                    "b": b,
                    "op": op,
                    "easier": easier,
                },
            }

    rng = _get_seed_rng(child_id, session_index, turn_n, salt)

    op = "+"
    a = 1
    b = 1
    answer = 2

    if skill_id == "count_10":
        op = "+"
        a = rng.randint(2, 6) if easier else rng.randint(2, 10)
        b = 0
        answer = a

    elif skill_id == "count_20":
        op = "+"
        a = rng.randint(11, 15) if easier else rng.randint(11, 20)
        b = 0
        answer = a

    elif skill_id == "one_more_less":
        # 0 = one more (+), 1 = one less (-)
        mode = rng.randint(0, 1)
        if mode == 0:
            op = "+"
            a = rng.randint(1, 10) if easier else rng.randint(1, 19)
            b = 1
            answer = a + 1
        else:
            op = "-"
            a = rng.randint(2, 10) if easier else rng.randint(2, 20)
            b = 1
            answer = a - 1

    elif skill_id == "bonds_5":
        op = "?"
        a = rng.randint(1, 3) if easier else rng.randint(1, 4)
        b = 5
        answer = 5 - a

    elif skill_id == "count_on":
        op = "+"
        # a from 2 to 9, b from 2 to 5 per spec 7.1
        a = rng.randint(2, 5) if easier else rng.randint(2, 9)
        b = rng.randint(2, 3) if easier else rng.randint(2, 5)
        answer = a + b

    elif skill_id == "add_5":
        op = "+"
        a = rng.randint(1, 2) if easier else rng.randint(1, 4)
        max_b = 5 - a
        b = rng.randint(1, max(1, max_b))
        answer = a + b

    elif skill_id == "sub_5":
        op = "-"
        a = rng.randint(2, 3) if easier else rng.randint(2, 5)
        b = rng.randint(1, a - 1)
        answer = a - b

    elif skill_id == "bonds_10":
        op = "?"
        a = rng.randint(1, 5) if easier else rng.randint(1, 9)
        b = 10
        answer = 10 - a

    elif skill_id == "add_10":
        op = "+"
        a = rng.randint(1, 5) if easier else rng.randint(1, 9)
        max_b = 10 - a
        b = rng.randint(1, max(1, max_b))
        answer = a + b

    elif skill_id == "sub_10":
        op = "-"
        a = rng.randint(3, 6) if easier else rng.randint(3, 10)
        b = rng.randint(1, a - 1)
        answer = a - b

    elif skill_id == "doubles":
        op = "+"
        a = rng.randint(1, 5) if easier else rng.randint(1, 10)
        b = a
        answer = 2 * a

    elif skill_id == "make_ten":
        op = "+"
        # sum 11 to 18
        a = rng.randint(6, 9)
        min_b = 11 - a
        max_b = 9
        b = rng.randint(min_b, max_b)
        answer = a + b

    elif skill_id == "add_20":
        op = "+"
        a = rng.randint(5, 12) if easier else rng.randint(5, 18)
        max_b = 20 - a
        b = rng.randint(1, max(1, max_b))
        answer = a + b

    else:
        # Fallback default
        op = "+"
        a = rng.randint(1, 5)
        b = rng.randint(1, 5)
        answer = a + b

    prob_id = f"prob_{child_id}_{session_index}_{turn_n}_{skill_id}_{a}_{b}_{salt}"
    return {
        "problem_id": prob_id,
        "skill_id": skill_id,
        "op": op,
        "a": a,
        "b": b,
        "answer": answer,
        "story_slots": {
            "object_set": object_set,
            "a": a,
            "b": b,
            "op": op,
            "easier": easier,
        },
    }


def parallel_problem(problem: dict[str, Any]) -> dict[str, Any]:
    """
    Generate a parallel problem of the same skill where:
    NO operand (a, b) and NO result (answer) equals the original answer.

    Crucial for Level 3 worked examples: guarantees the child is shown
    a worked example that never reveals the original problem's answer.
    """
    orig_answer = problem["answer"]
    skill_id = problem["skill_id"]

    for salt in range(1, 200):
        # Derive child_id and session info from problem_id or defaults
        cand = generate_problem(
            child_id="parallel_worker",
            skill_id=skill_id,
            session_index=99,
            turn_n=salt,
            salt=salt,
        )

        # Condition: no operand and no result equals orig_answer
        # and problem is distinct
        if (
            cand["a"] != orig_answer
            and cand["b"] != orig_answer
            and cand["answer"] != orig_answer
            and (cand["a"] != problem["a"] or cand["b"] != problem["b"])
        ):
            cand["problem_id"] = f"parallel_{problem['problem_id']}_{salt}"
            return cand

    # Safe deterministic fallback
    offset = 2 if orig_answer != 2 else 3
    cand_a = 1 if orig_answer != 1 else 2
    cand_b = offset if orig_answer != offset else offset + 1
    cand_ans = cand_a + cand_b
    if cand_ans == orig_answer:
        cand_b += 1
        cand_ans = cand_a + cand_b

    return {
        "problem_id": f"parallel_{problem['problem_id']}_fallback",
        "skill_id": skill_id,
        "op": "+",
        "a": cand_a,
        "b": cand_b,
        "answer": cand_ans,
        "story_slots": {
            "object_set": problem.get("story_slots", {}).get("object_set", "space"),
            "a": cand_a,
            "b": cand_b,
            "op": "+",
            "easier": False,
        },
    }
