"""
cartographer.py — Dynamic concept graph cartographer for MentoAI.

Expands concept definitions and semantic relationships (prerequisites, analogies,
components) on demand and writes them to FalkorDB (G9).
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.agents.runtime import AgentRuntime
from app.graph.embeddings import get_embedding
from app.graph.queries import record_concept_neighbourhood
from app.graph.models import ConceptNode

logger = logging.getLogger("mentoai.cartographer")
PROMPT_PATH = Path(__file__).parent / "prompts" / "cartographer.md"


class ConceptDefinition(BaseModel):
    key: str
    name: str
    summary: str
    domain: str = "general"


class ConceptRelationship(BaseModel):
    source: str
    target: str
    type: str = "PREREQUISITE_OF"
    why: str = ""


class CartographerResult(BaseModel):
    concepts: List[ConceptDefinition] = Field(default_factory=list)
    relationships: List[ConceptRelationship] = Field(default_factory=list)


class CartographerAgent:
    def __init__(self, runtime: Optional[AgentRuntime] = None):
        self.runtime = runtime or AgentRuntime()
        self.prompt_text = (
            PROMPT_PATH.read_text(encoding="utf-8")
            if PROMPT_PATH.exists()
            else "You are the Cartographer Agent for MentoAI."
        )

    def expand_concepts(
        self,
        graph_name: str,
        candidate_concepts: List[str],
        context_hint: str = "",
    ) -> CartographerResult:
        """
        Takes candidate concept names, defines them canonically, establishes edges,
        embeds them, and persists them via G9.
        """
        if not candidate_concepts:
            return CartographerResult()

        prompt = f"""
Candidate Concepts to Map:
{candidate_concepts}

Context:
{context_hint}

Define these concepts canonically and establish appropriate relationships (PREREQUISITE_OF, ANALOGOUS_TO, PART_OF, TOUCHES).
"""
        raw_res = self.runtime.call_structured(
            system_prompt=self.prompt_text,
            user_prompt=prompt,
            expected_schema=CartographerResult,
            tier="smart",
        )

        result = CartographerResult(**raw_res)

        # Convert to ConceptNode with embeddings
        concept_nodes = []
        for c in result.concepts:
            embedding = get_embedding(f"{c.name}: {c.summary}")
            concept_nodes.append(
                ConceptNode(
                    key=c.key,
                    name=c.name,
                    summary=c.summary,
                    domain=c.domain,
                    embedding=embedding,
                    created_by="Cartographer",
                )
            )

        # Build relationships list
        edges = []
        for rel in result.relationships:
            edges.append(
                {
                    "source": rel.source,
                    "target": rel.target,
                    "type": rel.type,
                    "props": {"why": rel.why, "confidence": 0.85},
                }
            )

        # Save to FalkorDB (G9)
        if concept_nodes or edges:
            try:
                record_concept_neighbourhood(
                    graph_name=graph_name,
                    concepts=concept_nodes,
                    relationships=edges,
                )
            except Exception as e:
                logger.warning(f"Failed to write concept neighbourhood: {e}")

        return result
