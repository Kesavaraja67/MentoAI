"""
api/sessions.py — Session lifecycle endpoints: start, submit answer, and end (consolidate).
"""
from __future__ import annotations

import uuid
from typing import Optional, Any
from fastapi import APIRouter, Header, HTTPException

from app.graph.client import get_graph
from app.graph.schema import build_session_graph
from app.graph.queries import q3_frontier_skill, q5_write_turn
from app.graph.consolidate import consolidate
from app.engines.problems import generate_problem, parallel_problem
from app.engines.assessor import assess_answer
from app.engines.mastery import update_confidence
from app.engines.planner import plan_next_step
from app.llm.client import chat
from app.llm.prompts import (
    build_tutor_system_prompt,
    build_tutor_user_payload,
    build_story_prompt,
)
from app.llm.validators import validate_tutor_output
from app.llm.templates import render_template
from app.graph.seed import PERSONAS
from app.models import (
    StartSessionRequest,
    StartSessionResponse,
    ProblemOut,
    AnswerRequest,
    AnswerResponse,
    EndSessionResponse,
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

# Active session in-memory state tracking for fast turn-by-turn context
# (Kept in sync with working memory session graph)
_ACTIVE_SESSIONS: dict[str, dict[str, Any]] = {}


def _get_persona_meta(child_id: str) -> dict:
    for p in PERSONAS:
        if p["id"] == child_id:
            return p
    return {"id": child_id, "name": child_id.title(), "age": 6, "interests": ["space"], "object_set": "space"}


@router.post("", response_model=StartSessionResponse)
def start_session(
    req: StartSessionRequest,
    x_llm_provider: Optional[str] = Header(None, alias="X-LLM-Provider"),
    x_llm_model: Optional[str] = Header(None, alias="X-LLM-Model"),
    x_llm_key: Optional[str] = Header(None, alias="X-LLM-Key"),
) -> StartSessionResponse:
    """
    Start a new learning session for a child:
    1. Hydrate working memory session_<session_id>
    2. Determine starting target skill (scripted opening problem, or Q3 frontier)
    3. Generate first problem
    4. Generate story frame
    """
    session_id = f"sess_{uuid.uuid4().hex[:10]}"
    persona = _get_persona_meta(req.child_id)

    # 1. Determine starting skill
    target_skill = "count_on" if req.child_id == "leo" else "count_10"
    if req.graph_mode == "on":
        cg = get_graph(f"child_{req.child_id}")
        frontier = q3_frontier_skill(cg)
        if frontier:
            target_skill = frontier["skill_id"]

    # 2. Hydrate session graph
    build_session_graph(
        child_id=req.child_id,
        session_id=session_id,
        graph_mode=req.graph_mode,
        target_skill_id=target_skill,
        origin_skill_id=target_skill,
    )

    # 3. Generate initial problem (turn_n = 0)
    prob_dict = generate_problem(
        child_id=req.child_id,
        skill_id=target_skill,
        session_index=1,
        turn_n=0,
    )

    # 4. Generate story frame wording
    story_text = ""
    if req.graph_mode == "on":
        story_messages = build_story_prompt(
            child_name=persona["name"],
            age=persona["age"],
            interest=persona["interests"][0] if persona.get("interests") else "space",
            object_set=persona.get("object_set", "rockets"),
            a=prob_dict["a"],
            b=prob_dict["b"],
            op=prob_dict["op"],
        )
        try:
            story_text = chat(
                story_messages,
                max_tokens=40,
                byok_provider=x_llm_provider,
                byok_model=x_llm_model,
                byok_key=x_llm_key,
            )
        except Exception:
            story_text = ""

    if not story_text:
        noun = persona.get("object_set", "rockets")
        story_text = f"Welcome {persona['name']}! Let's explore some shiny {noun} together."

    # Cache active problem details
    _ACTIVE_SESSIONS[session_id] = {
        "child_id": req.child_id,
        "graph_mode": req.graph_mode,
        "active_problem": prob_dict,
        "turn_n": 1,
        "attempts_on_problem": 0,
        "consecutive_correct": 0,
        "origin_skill": None,
        "current_skill": target_skill,
        "working_confidence": 0.35 if target_skill == "count_on" else 0.5,
    }

    return StartSessionResponse(
        session_id=session_id,
        problem=ProblemOut(**prob_dict),
        story=story_text,
    )


@router.post("/{session_id}/answer", response_model=AnswerResponse)
def submit_answer(
    session_id: str,
    req: AnswerRequest,
    x_llm_provider: Optional[str] = Header(None, alias="X-LLM-Provider"),
    x_llm_model: Optional[str] = Header(None, alias="X-LLM-Model"),
    x_llm_key: Optional[str] = Header(None, alias="X-LLM-Key"),
) -> AnswerResponse:
    """
    Submit an answer for the active problem:
    1. Assess correctness and classify misconception (code rules)
    2. Update working confidence
    3. Record turn in session graph
    4. Plan next step (advance, hint ladder, regress, praise)
    5. Generate validated tutor dialogue
    6. Return next problem if applicable
    """
    state = _ACTIVE_SESSIONS.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    curr_prob = state["active_problem"]
    child_id = state["child_id"]
    graph_mode = state["graph_mode"]
    persona = _get_persona_meta(child_id)
    curr_skill = state["current_skill"]
    curr_conf = state["working_confidence"]
    turn_n = state["turn_n"]
    attempts = state["attempts_on_problem"]
    consec_corr = state["consecutive_correct"]
    origin_skill = state["origin_skill"]

    # 1. Deterministic assessment
    is_correct, misconception_id = assess_answer(
        op=curr_prob["op"],
        a=curr_prob["a"],
        b=curr_prob["b"],
        answer=curr_prob["answer"],
        given=req.given,
    )

    # 2. Update confidence
    new_conf = update_confidence(
        current=curr_conf,
        correct=is_correct,
        hint_level=attempts if not is_correct else 0,
    )
    state["working_confidence"] = new_conf

    # 3. Log Turn in session graph
    sg = get_graph(f"session_{session_id}")
    try:
        q5_write_turn(
            sg,
            session_id=session_id,
            n=turn_n,
            problem_id=curr_prob["problem_id"],
            skill_id=curr_skill,
            op=curr_prob["op"],
            a=curr_prob["a"],
            b=curr_prob["b"],
            answer=curr_prob["answer"],
            given=req.given,
            correct=is_correct,
            misconception_id=misconception_id or "",
            hint_level=attempts + 1 if not is_correct else 0,
            hint_style="story",
        )
    except Exception:
        pass

    # 4. Plan next step
    outcome = plan_next_step(
        session_id=session_id,
        current_skill_id=curr_skill,
        correct=is_correct,
        working_confidence=new_conf,
        attempts_on_current_problem=attempts,
        consecutive_correct_on_skill=consec_corr,
        misconception_id=misconception_id,
        turn_n=turn_n,
        origin_skill=origin_skill,
        graph_mode=graph_mode,
    )

    state["consecutive_correct"] = outcome.new_consecutive_correct
    state["origin_skill"] = outcome.origin_skill

    # 5. Tutor Wording Generation
    tutor_text = ""
    noun = persona.get("object_set", "stars")

    if is_correct:
        state["attempts_on_problem"] = 0
        state["turn_n"] += 1
        tutor_text = "Wonderful job! You got it right. How did you figure it out?"

        # Generate next problem
        next_skill = outcome.next_skill_id
        state["current_skill"] = next_skill
        next_prob = generate_problem(
            child_id=child_id,
            skill_id=next_skill,
            session_index=1,
            turn_n=state["turn_n"],
        )
        state["active_problem"] = next_prob

        return AnswerResponse(
            correct=True,
            kind=outcome.kind,
            tutor_text=tutor_text,
            next_problem=ProblemOut(**next_prob),
            decision_ids=outcome.decision_ids,
            working_confidence=new_conf,
        )

    # Child was WRONG:
    state["attempts_on_problem"] += 1
    state["turn_n"] += 1

    if outcome.kind == "regress":
        state["attempts_on_problem"] = 0
        state["current_skill"] = outcome.next_skill_id
        tutor_text = "Let's take a friendly step together on a warm-up challenge!"
        regress_prob = generate_problem(
            child_id=child_id,
            skill_id=outcome.next_skill_id,
            session_index=1,
            turn_n=state["turn_n"],
            easier=outcome.easier,
        )
        state["active_problem"] = regress_prob

        return AnswerResponse(
            correct=False,
            kind="regress",
            tutor_text=tutor_text,
            next_problem=ProblemOut(**regress_prob),
            decision_ids=outcome.decision_ids,
            working_confidence=new_conf,
        )

    # Hint Ladder (levels 1, 2, 3)
    par_prob = None
    if outcome.hint_level == 3:
        par_prob = parallel_problem(curr_prob)

    if graph_mode == "on":
        sys_prompt = build_tutor_system_prompt(
            age=persona["age"],
            interest=persona["interests"][0] if persona.get("interests") else "space",
        )
        user_payload = build_tutor_user_payload(
            child_name=persona["name"],
            age=persona["age"],
            interests=persona["interests"],
            problem_text=f"{curr_prob['a']} {curr_prob['op']} {curr_prob['b']}",
            given_answer=req.given,
            misconception_id=misconception_id or "unclassified",
            hint_level=outcome.hint_level,
            hint_style=outcome.hint_style,
            weak_skill_name=outcome.weak_skill_id,
            parallel_problem=par_prob,
            object_noun=noun,
            a=curr_prob["a"],
            b=curr_prob["b"],
        )
        try:
            raw_text = chat(
                [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_payload}],
                max_tokens=50,
                byok_provider=x_llm_provider,
                byok_model=x_llm_model,
                byok_key=x_llm_key,
            )
            # Validate output against answer leak, length, question marks
            valid, reason = validate_tutor_output(
                raw_text,
                correct_answer=curr_prob["answer"],
                is_level_3=(outcome.hint_level == 3),
            )
            if valid:
                tutor_text = raw_text
        except Exception:
            pass

    # Deterministic fallback template if LLM failed, was empty, or violated safety
    if not tutor_text:
        par_a = par_prob["a"] if par_prob else 2
        par_b = par_prob["b"] if par_prob else 3
        par_ans = par_prob["answer"] if par_prob else 5

        tutor_text = render_template(
            style=outcome.hint_style,
            level=outcome.hint_level,
            misconception_id=misconception_id or "",
            name=persona["name"],
            noun=noun,
            a=curr_prob["a"],
            b=curr_prob["b"],
            par_a=par_a,
            par_b=par_b,
            par_ans=par_ans,
        )

    return AnswerResponse(
        correct=False,
        kind="hint",
        tutor_text=tutor_text,
        next_problem=None,  # Keep current problem active on wrong answer
        decision_ids=outcome.decision_ids,
        working_confidence=new_conf,
    )


@router.post("/{session_id}/end", response_model=EndSessionResponse)
def end_session(session_id: str) -> EndSessionResponse:
    """
    End session and run consolidation:
    - Folds working memory into child long-term graph
    - Computes memory diff
    - Cleans up transient session graph
    """
    diff = consolidate(session_id)
    if session_id in _ACTIVE_SESSIONS:
        del _ACTIVE_SESSIONS[session_id]

    return EndSessionResponse(
        skills=diff.get("skills", []),
        episode_id=diff.get("episode_id", ""),
        hint_style_changes=diff.get("hint_style_changes", []),
        summary=diff.get("summary", ""),
    )
