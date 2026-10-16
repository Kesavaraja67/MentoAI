"""
llm/validators.py — Safety and child-pedagogy validators for LLM outputs.

Per Section 8.3 of the specification:
Reject and regenerate once, then fall back to a template, if the output:
1. Contains the original correct answer as a whole-token digit or word (e.g. "7" or "seven", but not inside "17")
2. Exceeds 25 words
3. Exceeds 2 sentences
4. Contains words from the banned list ('wrong', 'incorrect', 'fail', 'bad', 'stupid')
5. Has more than one question mark
6. Is empty or whitespace only
"""
from __future__ import annotations

import re
from typing import Tuple

NUMBER_WORDS = {
    0: "zero", 1: "one", 2: "two", 3: "three", 4: "four",
    5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
    10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen",
    14: "fourteen", 15: "fifteen", 16: "sixteen", 17: "seventeen",
    18: "eighteen", 19: "nineteen", 20: "twenty",
}

BANNED_WORDS = {"wrong", "incorrect", "fail", "failed", "bad", "stupid"}


def count_sentences(text: str) -> int:
    """Count sentences based on punctuation (. ! ?)."""
    clean = text.strip()
    if not clean:
        return 0
    # Split on sentence ending punctuation
    parts = [s.strip() for s in re.split(r"[.!?]+", clean) if s.strip()]
    return len(parts)


def validate_tutor_output(
    text: str,
    correct_answer: int,
    is_level_3: bool = False,
) -> Tuple[bool, str]:
    """
    Validates tutor response against strict safety rules.
    Returns: (is_valid: bool, rejection_reason: str)
    """
    stripped = text.strip()
    if not stripped:
        return False, "Output is empty"

    # 1. Answer leak check (whole token digit or word)
    ans_digit_pattern = rf"\b{correct_answer}\b"
    if re.search(ans_digit_pattern, stripped):
        return False, f"Leaked answer digit: {correct_answer}"

    ans_word = NUMBER_WORDS.get(correct_answer)
    if ans_word:
        ans_word_pattern = rf"\b{ans_word}\b"
        if re.search(ans_word_pattern, stripped, re.IGNORECASE):
            return False, f"Leaked answer word: '{ans_word}'"

    # 2. Word count <= 25 words
    words = re.findall(r"\b\w+\b", stripped)
    if len(words) > 25:
        return False, f"Too long: {len(words)} words (max 25)"

    # 3. Sentence count <= 2 sentences
    num_sentences = count_sentences(stripped)
    if num_sentences > 2:
        return False, f"Too many sentences: {num_sentences} (max 2)"

    # 4. Banned words check
    lower_words = {w.lower() for w in words}
    banned_present = lower_words.intersection(BANNED_WORDS)
    if banned_present:
        return False, f"Contains banned word(s): {banned_present}"

    # 5. Question mark count <= 1
    q_count = stripped.count("?")
    if q_count > 1:
        return False, f"More than one question mark: {q_count} (max 1)"

    return True, ""
