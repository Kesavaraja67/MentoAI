"""
llm/prompts.py — Structured prompt builders for Tutor and Story generation.

CRITICAL INVARIANT (Spec Section 8.2):
The CORRECT ANSWER is NEVER passed to the LLM.
This guarantees by construction that the model cannot accidentally leak the answer.
"""
from __future__ import annotations

import json
from typing import Any, Optional


def build_tutor_system_prompt(age: int = 6, interest: str = "space") -> str:
    return (
        f"You are a kind tutor speaking to a child aged {age} who loves {interest}. "
        f"Follow these strict rules:\n"
        f"1. Reply in at most 2 short sentences and at most 25 words total.\n"
        f"2. Ask exactly ONE question to guide the child.\n"
        f"3. Be warm and encouraging.\n"
        f"4. NEVER say 'wrong', 'incorrect', 'bad', or 'fail'.\n"
        f"5. NEVER state, calculate, or hint at the final answer.\n"
        f"6. Use the interest ({interest}) in your guidance."
    )


def build_tutor_user_payload(
    child_name: str,
    age: int,
    interests: list[str],
    problem_text: str,
    given_answer: int,
    misconception_id: str,
    hint_level: int,
    hint_style: str,
    weak_skill_name: Optional[str] = None,
    parallel_problem: Optional[dict[str, Any]] = None,
    object_noun: str = "stars",
    a: int = 3,
    b: int = 4,
) -> str:
    """
    Constructs the structured JSON user prompt.
    Notice: the true answer is NOT in this dictionary.
    """
    payload: dict[str, Any] = {
        "child_name": child_name,
        "age": age,
        "interests": interests,
        "object_noun": object_noun,
        "problem_text": problem_text,
        "wrong_answer_given": given_answer,
        "misconception_id": misconception_id or "unclassified",
        "hint_level": hint_level,
        "hint_style": hint_style,
        "a": a,
        "b": b,
    }

    if weak_skill_name:
        payload["underlying_weak_skill"] = weak_skill_name

    if hint_level == 3 and parallel_problem:
        payload["parallel_worked_example"] = {
            "a": parallel_problem["a"],
            "b": parallel_problem["b"],
            "worked_answer": parallel_problem["answer"],
        }

    return json.dumps(payload)


def build_story_prompt(child_name: str, age: int, interest: str, object_set: str, a: int, b: int, op: str) -> list[dict]:
    """Build prompt for generating a short 1–2 sentence story frame for a problem."""
    sys = (
        f"You are a friendly storyteller for a child aged {age} who loves {interest}. "
        f"Write a 1-sentence math story introduction using {object_set}. "
        f"Keep it under 20 words. Do NOT reveal the answer."
    )
    user = f"Introduce a math problem with {a} and {b} {object_set} for {child_name}."
    return [{"role": "system", "content": sys}, {"role": "user", "content": user}]
