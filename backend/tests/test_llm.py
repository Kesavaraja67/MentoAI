"""
tests/test_llm.py — Unit tests for Phase 4 LLM layer.

Tests:
1. Validators:
   - Rejects answer leaks (digits and number words)
   - Rejects outputs > 25 words
   - Rejects outputs > 2 sentences
   - Rejects banned words ('wrong', 'incorrect', 'fail', 'bad', 'stupid')
   - Rejects more than 1 question mark
   - Accepts clean, compliant responses
2. Templates:
   - Every single template (12 style/level + 3 misconception) passes all validators!
3. Providers:
   - Approved allowlist (groq, openrouter, gemini, openai) maps to official URLs
   - Disallowed provider raises ValueError (SSRF protection)
4. Fake client:
   - Produces valid, compliant strings
5. Prompt invariant:
   - Correct answer is NEVER in the structured JSON user prompt
"""
from __future__ import annotations

import json
import pytest
from app.llm.validators import validate_tutor_output
from app.llm.providers import get_base_url, PROVIDER_BASE_URLS
from app.llm.templates import TEMPLATES, MISCONCEPTION_TEMPLATES, render_template
from app.llm.fake import fake_chat
from app.llm.prompts import build_tutor_user_payload


# ── 1. Validator Tests ────────────────────────────────────────────────────────

class TestValidators:
    def test_rejects_answer_digit_leak(self):
        # Correct answer is 7
        valid, reason = validate_tutor_output("The answer is 7 right now.", correct_answer=7)
        assert valid is False
        assert "Leaked answer digit" in reason

    def test_rejects_answer_word_leak(self):
        valid, reason = validate_tutor_output("Do you see seven rockets here?", correct_answer=7)
        assert valid is False
        assert "Leaked answer word" in reason

    def test_allows_digits_inside_other_numbers(self):
        # 7 inside 17 should NOT be flagged as a leak of 7
        valid, _ = validate_tutor_output("What about 17 items on screen?", correct_answer=7)
        assert valid is True

    def test_rejects_more_than_25_words(self):
        long_text = "This is a very long sentence designed specifically to exceed the maximum word count allowed by our strict twenty-five word limit for early childhood learners on this screen."
        valid, reason = validate_tutor_output(long_text, correct_answer=4)
        assert valid is False
        assert "Too long" in reason

    def test_rejects_more_than_2_sentences(self):
        three_sentences = "First sentence here. Second sentence goes here! Third sentence is one too many?"
        valid, reason = validate_tutor_output(three_sentences, correct_answer=4)
        assert valid is False
        assert "Too many sentences" in reason

    def test_rejects_banned_words(self):
        for banned in ["wrong", "incorrect", "fail", "bad", "stupid"]:
            text = f"That was {banned}, try again."
            valid, reason = validate_tutor_output(text, correct_answer=4)
            assert valid is False
            assert "banned word" in reason

    def test_rejects_multiple_question_marks(self):
        two_questions = "Is this right? What do you think?"
        valid, reason = validate_tutor_output(two_questions, correct_answer=4)
        assert valid is False
        assert "More than one question mark" in reason

    def test_accepts_clean_compliant_tutor_response(self):
        good = "Touch 3 rockets first, then count 4 more. How many in all?"
        valid, reason = validate_tutor_output(good, correct_answer=7)
        assert valid is True
        assert reason == ""


# ── 2. Template Validation ────────────────────────────────────────────────────

class TestTemplates:
    def test_all_templates_pass_validators(self):
        # For every (style, level) template:
        for (style, level) in TEMPLATES.keys():
            rendered = render_template(
                style=style,
                level=level,
                name="Leo",
                noun="rockets",
                a=3,
                b=4,
                par_a=2,
                par_b=3,
                par_ans=5,
            )
            # Original answer is 7
            valid, reason = validate_tutor_output(rendered, correct_answer=7)
            assert valid is True, f"Template ({style}, {level}) failed validation: {reason} | Text: '{rendered}'"

    def test_all_misconception_templates_pass_validators(self):
        for (mid, level) in MISCONCEPTION_TEMPLATES.keys():
            rendered = render_template(
                style="story",
                level=level,
                misconception_id=mid,
                name="Leo",
                noun="stars",
                a=3,
                b=4,
                par_a=2,
                par_b=3,
                par_ans=5,
            )
            valid, reason = validate_tutor_output(rendered, correct_answer=7)
            assert valid is True, f"Misconception template ({mid}, {level}) failed validation: {reason} | Text: '{rendered}'"


# ── 3. Provider Allowlist (SSRF Protection) ───────────────────────────────────

class TestProviders:
    def test_approved_providers_return_correct_urls(self):
        for prov in ["groq", "openrouter", "gemini", "openai"]:
            url = get_base_url(prov)
            assert url.startswith("https://")
            assert prov in PROVIDER_BASE_URLS

    def test_disallowed_provider_raises_error(self):
        with pytest.raises(ValueError) as exc:
            get_base_url("malicious-site.com")
        assert "not in the approved allowlist" in str(exc.value)


# ── 4. Prompt Safety Invariant ────────────────────────────────────────────────

class TestPrompts:
    def test_correct_answer_never_in_user_payload(self):
        payload_str = build_tutor_user_payload(
            child_name="Leo",
            age=6,
            interests=["space", "rockets"],
            problem_text="3 + 4",
            given_answer=6,  # wrong answer
            misconception_id="counts_start_number",
            hint_level=1,
            hint_style="story",
            weak_skill_name="Counting on",
            parallel_problem={"a": 2, "b": 3, "answer": 5},
            object_noun="rockets",
            a=3,
            b=4,
        )
        data = json.loads(payload_str)

        # Assert correct answer 7 is NOT anywhere in the keys or values
        assert "answer" not in data
        assert "correct_answer" not in data
        assert data["wrong_answer_given"] == 6
        assert 7 not in data.values()


# ── 5. Fake Client ────────────────────────────────────────────────────────────

class TestFakeClient:
    def test_fake_chat_produces_valid_response(self):
        payload_str = build_tutor_user_payload(
            child_name="Leo",
            age=6,
            interests=["space"],
            problem_text="3 + 4",
            given_answer=6,
            misconception_id="counts_start_number",
            hint_level=2,
            hint_style="visual",
            object_noun="rockets",
            a=3,
            b=4,
        )
        messages = [
            {"role": "system", "content": "You are a kind tutor."},
            {"role": "user", "content": payload_str},
        ]
        resp = fake_chat(messages)
        assert len(resp) > 0
        valid, reason = validate_tutor_output(resp, correct_answer=7)
        assert valid is True, f"Fake chat output invalid: {reason}"
