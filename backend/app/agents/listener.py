"""
listener.py — Post-turn comprehension listener for MentoAI.

Extracts Evidence of understanding/confusion, Misconceptions,
Curiosities, Interests, and Entities, writing them to FalkorDB (G8).
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.agents.runtime import AgentRuntime
from app.graph.queries import record_evidence
from app.graph.client import get_graph

logger = logging.getLogger("mentoai.listener")
PROMPT_PATH = Path(__file__).parent / "prompts" / "listener.md"


class EvidenceItem(BaseModel):
    concept_key: str = Field(default="general_curiosity")
    kind: str = Field(default="explained")
    quote: str = Field(default="")
    verdict: str = Field(default="demonstrated")
    strength: float = Field(default=0.8)
    new_depth: float = Field(default=0.5)
    new_confidence: float = Field(default=0.7)
    rationale: str = Field(default="")


class CuriosityItem(BaseModel):
    text: str
    intensity: float = 0.8


class InterestItem(BaseModel):
    name: str
    summary: str = ""


class EntityItem(BaseModel):
    name: str
    kind: str = "object"
    facts: List[str] = Field(default_factory=list)


class ListenerResult(BaseModel):
    evidence: List[EvidenceItem] = Field(default_factory=list)
    curiosities: List[CuriosityItem] = Field(default_factory=list)
    interests: List[InterestItem] = Field(default_factory=list)
    entities: List[EntityItem] = Field(default_factory=list)
    register_update: Optional[str] = None


class ListenerAgent:
    def __init__(self, runtime: Optional[AgentRuntime] = None):
        self.runtime = runtime or AgentRuntime()
        self.prompt_text = (
            PROMPT_PATH.read_text(encoding="utf-8")
            if PROMPT_PATH.exists()
            else "You are the Listener Agent for MentoAI."
        )

    def process_turn(
        self,
        graph_name: str,
        learner_id: str,
        turn_id: str,
        user_utterance: str,
        assistant_reply: str,
    ) -> ListenerResult:
        """
        Analyzes the turn, extracts learning indicators, and writes Evidence to FalkorDB.
        """
        prompt = f"""
Turn Transcript:
Person: "{user_utterance}"
MentoAI: "{assistant_reply}"

Analyze this dialogue and output structured JSON extracting evidence, curiosities, interests, entities, and register updates.
"""
        raw_result = self.runtime.call_structured(
            system_prompt=self.prompt_text,
            user_prompt=prompt,
            expected_schema=ListenerResult,
            tier="fast",
        )

        result = ListenerResult(**raw_result)

        # Write Evidence to FalkorDB (G8)
        for ev in result.evidence:
            try:
                record_evidence(
                    graph_name=graph_name,
                    learner_id=learner_id,
                    turn_id=turn_id,
                    concept_key=ev.concept_key,
                    kind=ev.kind,
                    quote=ev.quote or user_utterance[:100],
                    verdict=ev.verdict,
                    strength=ev.strength,
                    depth=ev.new_depth,
                    confidence=ev.new_confidence,
                    rationale=ev.rationale or "Extracted by Listener agent",
                )
            except Exception as e:
                logger.warning(f"Failed to write evidence to graph for {ev.concept_key}: {e}")

        # Persist Curiosities, Interests, and Entities if any were detected
        try:
            graph = get_graph(graph_name)
            for c in result.curiosities:
                graph.query(
                    """
                    MATCH (l:Learner {id: $lid})
                    CREATE (cur:Curiosity {
                        id: randomUUID(),
                        text: $text,
                        intensity: $intensity,
                        status: 'open'
                    })
                    CREATE (l)-[:WONDERS]->(cur)
                    """,
                    {"lid": learner_id, "text": c.text, "intensity": c.intensity},
                )
            for i in result.interests:
                graph.query(
                    """
                    MATCH (l:Learner {id: $lid})
                    MERGE (intr:Interest {name: $name})
                    ON CREATE SET intr.summary = $summary
                    MERGE (l)-[r:LOVES]->(intr)
                    ON CREATE SET r.strength = 0.8
                    ON MATCH SET r.strength = r.strength + 0.1
                    """,
                    {"lid": learner_id, "name": i.name, "summary": i.summary},
                )
            for ent in result.entities:
                graph.query(
                    """
                    MATCH (l:Learner {id: $lid})
                    MERGE (e:Entity {name: $name})
                    ON CREATE SET e.id = randomUUID(), e.kind = $kind, e.facts = $facts
                    MERGE (l)-[m:MENTIONED]->(e)
                    ON CREATE SET m.times = 1, m.last_ts = timestamp()
                    ON MATCH SET m.times = m.times + 1, m.last_ts = timestamp()
                    """,
                    {
                        "lid": learner_id,
                        "name": ent.name,
                        "kind": ent.kind,
                        "facts": ent.facts,
                    },
                )
        except Exception as e:
            logger.warning(f"Failed to persist curiosity/interest/entity to graph: {e}")

        return result
