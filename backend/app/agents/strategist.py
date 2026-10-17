"""
strategist.py — Pedagogical reasoning agent for MentoAI.

Formulates plans and records decisions with explicit BECAUSE provenance edges
grounded in graph traversals (G3 bridge paths, G4 weak prerequisites, G5 style outcomes).
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.agents.runtime import AgentRuntime
from app.graph.queries import (
    get_bridge_paths,
    get_weak_prerequisites,
    get_style_outcomes,
    get_open_loops_ranked,
    record_decision,
)
from app.graph.client import get_graph

logger = logging.getLogger("mentoai.strategist")
PROMPT_PATH = Path(__file__).parent / "prompts" / "strategist.md"


class BecauseItem(BaseModel):
    type: str = "evidence"
    description: str = ""
    node_ref: Optional[str] = None


class DecisionOutput(BaseModel):
    kind: str = "pedagogical_guidance"
    chosen_move: str = "analogy"
    target_concept: Optional[str] = None
    rationale: str = ""
    confidence: float = 0.85
    because_items: List[BecauseItem] = Field(default_factory=list)


class StrategistResult(BaseModel):
    plan_text: str = Field(default="Encourage curiosity and explore connections.")
    decision: DecisionOutput = Field(default_factory=DecisionOutput)


class StrategistAgent:
    def __init__(self, runtime: Optional[AgentRuntime] = None):
        self.runtime = runtime or AgentRuntime()
        self.prompt_text = (
            PROMPT_PATH.read_text(encoding="utf-8")
            if PROMPT_PATH.exists()
            else "You are the Strategist Agent for MentoAI."
        )

    def plan_next_turn(
        self,
        graph_name: str,
        learner_id: str,
        turn_id: str,
        recent_concept: Optional[str] = None,
        recent_evidence_ids: Optional[List[str]] = None,
    ) -> StrategistResult:
        """
        Executes graph traversals to find bridges and weak prerequisites,
        then synthesizes an informed Plan and Decision with BECAUSE edges.
        """
        bridge_info = []
        weak_prereqs = []
        if recent_concept:
            try:
                bridge_info = get_bridge_paths(graph_name, learner_id, recent_concept)
            except Exception as e:
                logger.warning(f"Error querying bridge paths: {e}")
            try:
                weak_prereqs = get_weak_prerequisites(graph_name, learner_id, recent_concept)
            except Exception as e:
                logger.warning(f"Error querying weak prerequisites: {e}")

        style_outcomes = []
        try:
            style_outcomes = get_style_outcomes(graph_name, learner_id)
        except Exception as e:
            logger.warning(f"Error querying style outcomes: {e}")

        prompt = f"""
Learner ID: {learner_id}
Recent Concept: {recent_concept or 'Exploration'}

Graph Memory Insights:
- Bridge Paths: {[b.model_dump() if hasattr(b, 'model_dump') else b for b in bridge_info] if bridge_info else 'None found'}
- Weak Prerequisites: {[w.model_dump() if hasattr(w, 'model_dump') else w for w in weak_prereqs] if weak_prereqs else 'None identified'}
- Teaching Move Success: {[s.model_dump() if hasattr(s, 'model_dump') else s for s in style_outcomes] if style_outcomes else 'Default profile'}

Formulate a concise pedagogical plan and decision citing graph reasons.
"""
        raw_res = self.runtime.call_structured(
            system_prompt=self.prompt_text,
            user_prompt=prompt,
            expected_schema=StrategistResult,
            tier="smart",
        )

        plan_text = raw_res.get("plan_text", raw_res.get("plan", "Continue engaging inquiry."))
        dec_dict = raw_res.get("decision", {})
        decision = DecisionOutput(
            kind=dec_dict.get("kind", "pedagogical_guidance"),
            chosen_move=dec_dict.get("chosen_move", raw_res.get("teaching_move", "analogy")),
            target_concept=dec_dict.get("target_concept", recent_concept),
            rationale=dec_dict.get("rationale", "Guided by learner's demonstrated curiosity."),
            confidence=float(dec_dict.get("confidence", 0.85)),
            because_items=[BecauseItem(**b) if isinstance(b, dict) else BecauseItem(description=str(b)) for b in dec_dict.get("because_items", [])],
        )

        # Write Decision and Plan to FalkorDB (G10)
        try:
            because_ids = recent_evidence_ids or ([turn_id] if turn_id else [])
            record_decision(
                graph_name=graph_name,
                agent_name="Strategist",
                kind=decision.kind,
                chosen_move=decision.chosen_move,
                rationale=decision.rationale,
                confidence=decision.confidence,
                target_concept=decision.target_concept,
                turn_id=turn_id,
                because_ids=because_ids,
            )

            # Store plan in graph for context assembly
            graph = get_graph(graph_name)
            graph.query(
                """
                MATCH (l:Learner {id: $lid})
                CREATE (p:Plan {
                    id: randomUUID(),
                    text: $plan,
                    ts: timestamp(),
                    consumed: false
                })
                CREATE (l)-[:HAS_PLAN]->(p)
                """,
                {"lid": learner_id, "plan": plan_text},
            )
        except Exception as e:
            logger.warning(f"Failed to record strategist decision/plan in graph: {e}")

        return StrategistResult(plan_text=plan_text, decision=decision)
