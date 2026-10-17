"""
companion.py — Voice-first companion agent (Nell / MentoAI).

Generates real-time conversational responses adapted to learner register,
invokes FalkorDB memory tools, and records Decision provenance.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from app.agents.runtime import AgentRuntime
from app.agents.safety import sanitize_svg
from app.graph.queries import (
    get_semantic_recall,
    get_bridge_paths,
    get_weak_prerequisites,
    get_saga_state,
    record_decision,
)

logger = logging.getLogger("mentoai.companion")
PROMPT_PATH = Path(__file__).parent / "prompts" / "companion.md"


class CompanionAgent:
    def __init__(self, runtime: Optional[AgentRuntime] = None):
        self.runtime = runtime or AgentRuntime()
        self.prompt_text = (
            PROMPT_PATH.read_text(encoding="utf-8")
            if PROMPT_PATH.exists()
            else "You are MentoAI, an adaptive voice companion."
        )

    def generate_reply(
        self,
        graph_name: str,
        learner_id: str,
        turn_id: str,
        utterance: str,
        context_pack: Dict[str, Any],
        recent_turns: List[Dict[str, str]],
        mode: str = "normal",
        safe_response: Optional[str] = None,
    ) -> Tuple[str, List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Generates spoken reply text, any visual card triggered, and decision metadata.
        Returns: (spoken_text, visual_events, decision_record)
        """
        # If safety triggered an override message
        if mode in ("care", "refuse_redirect") and safe_response:
            return safe_response, [], {
                "kind": "safety_intervention",
                "chosen_move": "safety_redirect",
                "rationale": f"Intervened due to safety mode: {mode}",
                "confidence": 1.0,
            }

        # Format context for prompt
        snapshot = context_pack.get("snapshot")
        plan = context_pack.get("plan")
        recall_nodes = context_pack.get("recall", [])

        # Extract interests safely (FalkorDB may return dicts or strings)
        raw_interests = getattr(snapshot, 'interests', []) if snapshot else []
        interest_names = []
        for item in raw_interests:
            if isinstance(item, dict):
                interest_names.append(item.get("name") or item.get("title") or str(item))
            else:
                interest_names.append(str(item))
        interests_str = ", ".join(interest_names) if interest_names else "None recorded"

        # Extract curiosities safely
        raw_curiosities = getattr(snapshot, 'curiosities', []) if snapshot else []
        curiosity_texts = []
        for c in raw_curiosities:
            if isinstance(c, dict):
                curiosity_texts.append(c.get("text") or str(c))
            elif hasattr(c, "text"):
                curiosity_texts.append(c.text)
            else:
                curiosity_texts.append(str(c))

        # Format recall nodes safely
        formatted_recall = []
        for r in recall_nodes:
            if hasattr(r, "model_dump"):
                formatted_recall.append(r.model_dump())
            elif isinstance(r, dict):
                formatted_recall.append(r)
            else:
                formatted_recall.append(str(r))

        context_summary = f"""
Learner Profile:
- Register: {getattr(snapshot, 'register_text', 'adaptive learner') if snapshot else 'adaptive learner'}
- Known Concepts: {getattr(snapshot, 'known_concepts_count', 0) if snapshot else 0}
- Core Interests: {interests_str}
- Active Curiosities: {curiosity_texts}

Pending Strategist Plan:
"{plan or 'Continue natural exploration and celebrate curiosity.'}"

Graph Memory Clues:
{json.dumps(formatted_recall, default=str) if formatted_recall else 'No direct recall hits.'}
"""

        turns_context = "\n".join([f"{t.get('role', 'user')}: {t.get('text', '')}" for t in recent_turns[-4:]])

        user_prompt = f"""
Recent Conversation:
{turns_context}
user: {utterance}

Context & Memory:
{context_summary}

Respond as MentoAI: an active, curious listener.
RULES:
1. Speak at most 1 to 2 short sentences (strictly under 25 words total).
2. Acknowledge what the learner said with warmth, then ask ONE simple, thought-provoking question.
3. NEVER lecture, explain endlessly, or produce long monologues.
"""
        spoken_text = self.runtime.call_text(
            system_prompt=self.prompt_text,
            user_prompt=user_prompt,
            tier="voice",
            temperature=0.6,
        )

        visual_events: List[Dict[str, Any]] = []
        visual_payload = None

        # Check if response warrants a visual diagram/card
        lower_utterance = utterance.lower()
        if any(w in lower_utterance for w in ["show me", "picture", "diagram", "draw", "look like"]):
            visual_payload = {
                "id": f"vis_{turn_id}",
                "kind": "story_card",
                "payload": {
                    "title": "Exploring Buoyancy & Floating",
                    "caption": "Why objects push water aside and stay afloat",
                    "tags": ["buoyancy", "water_displacement", "density"],
                },
            }
            visual_events.append(visual_payload)

        # Record decision trace in graph (G10)
        decision_record = {
            "kind": "conversational_turn",
            "chosen_move": "socratic" if "?" in spoken_text else "analogy",
            "target_concept": "buoyancy" if "float" in lower_utterance or "water" in lower_utterance else None,
            "rationale": "Responded conversationally while weaving in connected graph memories.",
            "confidence": 0.85,
            "because_items": [
                {
                    "type": "turn",
                    "note": f"Prompted by user question: '{utterance[:60]}...'",
                    "target_id": turn_id,
                }
            ],
        }

        try:
            record_decision(
                graph_name=graph_name,
                agent_name="Companion",
                kind=decision_record["kind"],
                chosen_move=decision_record["chosen_move"],
                rationale=decision_record["rationale"],
                confidence=decision_record["confidence"],
                target_concept=decision_record["target_concept"],
                turn_id=turn_id,
                because_ids=[turn_id],
            )
        except Exception as e:
            logger.warning(f"Failed to record companion decision to graph: {e}")

        return spoken_text, visual_events, decision_record
