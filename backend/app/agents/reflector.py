"""
reflector.py — Session consolidation and adult digest agent for MentoAI.

Runs at session end to consolidate memories, summarize dialogues,
update open loops, and generate a grown-up digest for parents/teachers.
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.agents.runtime import AgentRuntime
from app.graph.client import get_graph
from app.graph.queries import get_duplicate_candidates, merge_duplicate_concepts

logger = logging.getLogger("mentoai.reflector")
PROMPT_PATH = Path(__file__).parent / "prompts" / "reflector.md"


class AdultDigest(BaseModel):
    topics_explored: List[str] = Field(default_factory=list)
    strengths_demonstrated: List[str] = Field(default_factory=list)
    shaky_areas: List[str] = Field(default_factory=list)
    sparked_interests: List[str] = Field(default_factory=list)
    suggested_offline_activities: List[str] = Field(default_factory=list)
    note_for_grownup: str = ""


class OpenLoopItem(BaseModel):
    text: str
    kind: str = "curiosity"
    priority: str = "medium"
    related_concept: Optional[str] = None


class ReflectorResult(BaseModel):
    summary: str = ""
    mood_arc: str = "curious"
    open_loops: List[OpenLoopItem] = Field(default_factory=list)
    digest: AdultDigest = Field(default_factory=AdultDigest)


class ReflectorAgent:
    def __init__(self, runtime: Optional[AgentRuntime] = None):
        self.runtime = runtime or AgentRuntime()
        self.prompt_text = (
            PROMPT_PATH.read_text(encoding="utf-8")
            if PROMPT_PATH.exists()
            else "You are the Reflector Agent for MentoAI."
        )

    def consolidate_session(
        self,
        graph_name: str,
        learner_id: str,
        conversation_id: str,
        turns: List[Dict[str, str]],
    ) -> ReflectorResult:
        """
        Consolidates the completed conversation, persists summary and digest,
        and manages open loops and concept deduplication.
        """
        dialogue_text = "\n".join([f"{t.get('role', 'user')}: {t.get('text', '')}" for t in turns])

        prompt = f"""
Conversation Transcript:
{dialogue_text}

Generate a concise session summary, mood arc, open loops to follow up on, and an adult digest for a parent or educator.
"""
        raw_res = self.runtime.call_structured(
            system_prompt=self.prompt_text,
            user_prompt=prompt,
            expected_schema=ReflectorResult,
            tier="smart",
        )

        digest_raw = raw_res.get("adult_digest", raw_res.get("digest", {}))
        if isinstance(digest_raw, str):
            digest_obj = AdultDigest(note_for_grownup=digest_raw)
        else:
            digest_obj = AdultDigest(**digest_raw)

        open_loops = [
            OpenLoopItem(**ol) if isinstance(ol, dict) else OpenLoopItem(text=str(ol))
            for ol in raw_res.get("open_loops", [])
        ]

        result = ReflectorResult(
            summary=raw_res.get("summary", "Conversation completed with active exploration."),
            mood_arc=raw_res.get("mood_arc", "engaged"),
            open_loops=open_loops,
            digest=digest_obj,
        )

        # Write to FalkorDB
        try:
            graph = get_graph(graph_name)
            # Update Conversation node with summary and ended_at
            graph.query(
                """
                MATCH (c:Conversation {id: $cid})
                SET c.summary = $summary, c.mood_arc = $mood, c.ended_at = timestamp()
                """,
                {"cid": conversation_id, "summary": result.summary, "mood": result.mood_arc},
            )

            # Create Digest node linked to Conversation and Learner
            graph.query(
                """
                MATCH (l:Learner {id: $lid}), (c:Conversation {id: $cid})
                CREATE (d:Digest {
                    id: randomUUID(),
                    text: $note,
                    topics: $topics,
                    strengths: $strengths,
                    shaky_areas: $shaky,
                    offline_activities: $activities,
                    ts: timestamp()
                })
                CREATE (d)-[:SUMMARISES]->(c)
                CREATE (l)-[:HAS_DIGEST]->(d)
                """,
                {
                    "lid": learner_id,
                    "cid": conversation_id,
                    "note": result.digest.note_for_grownup,
                    "topics": result.digest.topics_explored,
                    "strengths": result.digest.strengths_demonstrated,
                    "shaky": result.digest.shaky_areas,
                    "activities": result.digest.suggested_offline_activities,
                },
            )

            # Store OpenLoop nodes
            for ol in result.open_loops:
                graph.query(
                    """
                    MATCH (l:Learner {id: $lid})
                    CREATE (loop:OpenLoop {
                        id: randomUUID(),
                        text: $text,
                        kind: $kind,
                        priority: $priority,
                        status: 'open',
                        ts: timestamp()
                    })
                    CREATE (l)-[:HAS_OPEN_LOOP]->(loop)
                    """,
                    {"lid": learner_id, "text": ol.text, "kind": ol.kind, "priority": ol.priority},
                )

            # Concept deduplication check (G13)
            candidates = get_duplicate_candidates(graph_name, threshold=0.92)
            for pair in candidates[:3]:
                # Merge if score is very high
                merge_duplicate_concepts(graph_name, canonical_key=pair["key1"], duplicate_key=pair["key2"])

        except Exception as e:
            logger.warning(f"Error persisting session reflection to graph: {e}")

        return result
