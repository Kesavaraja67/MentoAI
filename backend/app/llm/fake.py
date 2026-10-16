"""
llm/fake.py — Deterministic fake LLM client for testing and offline demo mode.

Produces deterministic outputs that strictly comply with all spec rules:
- At most 2 sentences and 25 words
- Asks at most one question
- Contains zero banned words
- Never leaks the correct answer
"""
from __future__ import annotations

import json
from app.llm.templates import render_template


def fake_chat(messages: list[dict], max_tokens: int = 60, temperature: float = 0.2) -> str:
    """
    Deterministic fake response generator.
    Parses the structured user message and returns a template-backed response.
    """
    user_content = ""
    for m in messages:
        if m.get("role") == "user":
            user_content = m.get("content", "")

    # Try parsing JSON payload from prompt
    try:
        data = json.loads(user_content)
        style = data.get("hint_style", "story")
        level = data.get("hint_level", 1)
        mid = data.get("misconception_id", "")
        name = data.get("child_name", "Friend")
        noun = data.get("object_noun", "stars")
        a = data.get("a", 3)
        b = data.get("b", 4)
        par = data.get("parallel_problem") or {}
        par_a = par.get("a", 2)
        par_b = par.get("b", 3)
        par_ans = par.get("answer", 5)

        return render_template(
            style=style,
            level=level,
            misconception_id=mid,
            name=name,
            noun=noun,
            a=a,
            b=b,
            par_a=par_a,
            par_b=par_b,
            par_ans=par_ans,
        )
    except Exception:
        # If prompt was free text (e.g. story frame or episode summary)
        if "story" in user_content.lower():
            return "Look at the shiny rockets waiting on the launchpad. How many can you count?"
        if "summary" in user_content.lower():
            return "Great math session today! Leo practiced counting on and solved the space challenges."

        return "How many items do you see in all?"
