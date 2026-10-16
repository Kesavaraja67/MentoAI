"""
engines/assessor.py — Deterministic answer assessment & misconception classification.

Pure deterministic rules per Section 7.2 of the specification.
The LLM is NEVER used to judge correctness or diagnose misconceptions.

Rule priority order (first match wins):
1. op == '+' and given == answer - 1 -> counts_start_number
2. op == '+' and given == answer + 1 -> overshoots_by_one
3. op == '-' and given == a + b      -> adds_instead_of_subtracts
4. op == '+' and given == abs(a - b) -> subtracts_instead_of_adds
5. op == '+' and given in (a, b)     -> reports_an_addend
6. otherwise                         -> unclassified
"""
from __future__ import annotations

from typing import Tuple, Optional


def assess_answer(
    op: str,
    a: int,
    b: int,
    answer: int,
    given: int,
) -> Tuple[bool, Optional[str]]:
    """
    Evaluates a child's given answer against the expected answer and classifies
    the error into one of the 5 canonical misconceptions or 'unclassified'.

    Returns:
        (is_correct: bool, misconception_id: str | None)
    """
    if given == answer:
        return True, None

    # Deterministic misconception classification
    if op == "+" and given == answer - 1:
        return False, "counts_start_number"

    if op == "+" and given == answer + 1:
        return False, "overshoots_by_one"

    if op == "-" and given == (a + b):
        return False, "adds_instead_of_subtracts"

    if op == "+" and given == abs(a - b):
        return False, "subtracts_instead_of_adds"

    if op == "+" and given in (a, b):
        return False, "reports_an_addend"

    return False, "unclassified"
