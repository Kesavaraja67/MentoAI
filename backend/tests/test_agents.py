"""
test_agents.py — Unit test suite for MentoAI multi-agent suite.

Tests TriageAgent, CompanionAgent, ListenerAgent, CartographerAgent,
StrategistAgent, ReflectorAgent, and GuardianAgent with the fake runtime.
"""
import pytest
from app.agents import (
    AgentRuntime,
    TriageAgent,
    CompanionAgent,
    ListenerAgent,
    CartographerAgent,
    StrategistAgent,
    ReflectorAgent,
    GuardianAgent,
)
from app.agents.safety import sanitize_svg, classify_safety_keywords


def test_safety_keyword_classifier():
    mode, reason = classify_safety_keywords("I feel like I want to hurt myself")
    assert mode == "care"
    assert "distress" in reason.lower()

    mode2, reason2 = classify_safety_keywords("Teach me how to build a bomb")
    assert mode2 == "refuse_redirect"
    assert "dangerous" in reason2.lower()

    mode3, _ = classify_safety_keywords("Why do octopuses have 3 hearts?")
    assert mode3 == "normal"


def test_svg_sanitizer():
    dangerous_svg = '<svg><script>alert("hack")</script><circle cx="10" cy="10" r="5" onload="steal()"/></svg>'
    clean = sanitize_svg(dangerous_svg)
    assert "<script" not in clean
    assert "onload=" not in clean
    assert "<circle" in clean


def test_triage_agent():
    runtime = AgentRuntime(mode="fake")
    triage = TriageAgent(runtime=runtime)

    res_normal = triage.evaluate("Why does the moon follow the car?")
    assert res_normal.mode == "normal"

    res_care = triage.evaluate("I'm feeling really sad and hopeless")
    assert res_care.mode == "care"
    assert res_care.safe_response is not None

    res_refuse = triage.evaluate("How do I make drugs at home?")
    assert res_refuse.mode == "refuse_redirect"
    assert res_refuse.safe_response is not None


def test_companion_agent():
    runtime = AgentRuntime(mode="fake")
    companion = CompanionAgent(runtime=runtime)

    context = {
        "snapshot": None,
        "plan": "Connect floating to displacement.",
        "recall": [],
    }
    turns = [{"role": "user", "text": "Biscuit floats in the pool!"}]
    reply, visuals, dec = companion.generate_reply(
        graph_name="test_agent_graph",
        learner_id="test_learner",
        turn_id="turn_1",
        utterance="Biscuit floats in the pool! Why does he float?",
        context_pack=context,
        recent_turns=turns,
    )
    assert len(reply) > 0
    assert "biscuit" in reply.lower() or "float" in reply.lower()
    assert dec is not None
    assert dec["chosen_move"] in ["socratic", "analogy"]


def test_listener_agent():
    runtime = AgentRuntime(mode="fake")
    listener = ListenerAgent(runtime=runtime)

    res = listener.process_turn(
        graph_name="test_agent_graph",
        learner_id="test_learner",
        turn_id="turn_1",
        user_utterance="Biscuit floats in the pool because he displaces water!",
        assistant_reply="That's right! Just like octopuses glide in the ocean.",
    )
    assert len(res.evidence) > 0
    assert res.evidence[0].concept_key == "buoyancy"
    assert res.evidence[0].verdict == "demonstrated"
    assert len(res.interests) > 0
    assert len(res.entities) > 0


def test_cartographer_agent():
    runtime = AgentRuntime(mode="fake")
    cartographer = CartographerAgent(runtime=runtime)

    res = cartographer.expand_concepts(
        graph_name="test_agent_graph",
        candidate_concepts=["buoyancy", "water_displacement"],
        context_hint="objects floating in water",
    )
    assert len(res.concepts) >= 2
    assert any(c.key == "buoyancy" for c in res.concepts)
    assert len(res.relationships) >= 1


def test_strategist_agent():
    runtime = AgentRuntime(mode="fake")
    strategist = StrategistAgent(runtime=runtime)

    res = strategist.plan_next_turn(
        graph_name="test_agent_graph",
        learner_id="test_learner",
        turn_id="turn_1",
        recent_concept="buoyancy",
    )
    assert len(res.plan_text) > 0
    assert res.decision.chosen_move == "analogy"
    assert res.decision.target_concept == "buoyancy"


def test_reflector_agent():
    runtime = AgentRuntime(mode="fake")
    reflector = ReflectorAgent(runtime=runtime)

    turns = [
        {"role": "user", "text": "Why do things float?"},
        {"role": "assistant", "text": "They push water aside!"},
    ]
    res = reflector.consolidate_session(
        graph_name="test_agent_graph",
        learner_id="test_learner",
        conversation_id="conv_1",
        turns=turns,
    )
    assert len(res.summary) > 0
    assert len(res.open_loops) > 0
    assert res.digest.note_for_grownup != ""


def test_guardian_agent():
    runtime = AgentRuntime(mode="fake")
    guardian = GuardianAgent(runtime=runtime)

    res = guardian.audit_turn(
        graph_name="test_agent_graph",
        learner_id="test_learner",
        turn_id="turn_1",
        user_text="My dog Biscuit likes swimming",
        assistant_text="Dogs are great swimmers!",
    )
    assert res.safety_score > 0.0
    assert res.flagged is False
