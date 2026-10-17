"""
models.py — Data models for MentoAI's FalkorDB graph schema.

Defines the 19 node schemas and typed edge properties described in SPEC Section 6.
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Node Models
# ---------------------------------------------------------------------------

class LearnerNode(BaseModel):
    id: str
    display_name: str
    created_at: str
    language: str = "en"
    register_text: str = "curious beginner, plain conversational vocabulary"
    register_conf: float = 0.5
    voice_pref: str = "natural"
    expires_at: Optional[str] = None


class ConversationNode(BaseModel):
    id: str
    title: str = "Conversation"
    started_at: str
    ended_at: Optional[str] = None
    summary: Optional[str] = None
    mood_arc: Optional[str] = None


class TurnNode(BaseModel):
    id: str
    idx: int
    role: Literal["person", "mentoai"]
    text: str
    spoken_text: Optional[str] = None
    ts: str
    emotion: Optional[str] = None
    intent: Optional[str] = None
    mode: Literal["normal", "care", "refuse_redirect"] = "normal"


class ConceptNode(BaseModel):
    key: str
    name: str
    summary: str
    domain: str = "general"
    embedding: Optional[List[float]] = None
    created_by: str = "cartographer"
    created_at: str


class EvidenceNode(BaseModel):
    id: str
    kind: Literal["explained", "applied", "asked", "misused", "teachback", "guessed"]
    quote: str
    verdict: Literal["demonstrated", "emerging", "confused", "neutral"]
    strength: float = 0.5
    ts: str


class MisconceptionNode(BaseModel):
    id: str
    statement: str
    status: Literal["open", "resolving", "resolved"] = "open"
    first_seen: str
    last_seen: str


class CuriosityNode(BaseModel):
    id: str
    text: str
    intensity: float = 0.5
    status: Literal["open", "explored", "parked"] = "open"


class InterestNode(BaseModel):
    name: str
    summary: str = ""


class EntityNode(BaseModel):
    id: str
    name: str
    kind: Literal["person", "pet", "place", "object"]
    facts: List[str] = Field(default_factory=list)


class TaleNode(BaseModel):
    id: str
    title: str
    premise: str
    status: Literal["active", "completed", "paused"] = "active"
    last_summary: Optional[str] = None


class ChapterNode(BaseModel):
    id: str
    idx: int
    text: str
    cliffhanger: Optional[str] = None
    ts: str


class TeachingMoveNode(BaseModel):
    name: Literal[
        "analogy",
        "story",
        "socratic",
        "worked_example",
        "hands_on",
        "retrieval",
        "humour",
        "visual",
        "silence",
        "reframe",
    ]


class PlanNode(BaseModel):
    id: str
    for_conversation: str
    text: str
    ts: str
    consumed: bool = False


class DecisionNode(BaseModel):
    id: str
    agent: str
    kind: Literal["pedagogical", "story", "bridge", "triage", "consolidation"]
    rationale: str
    ts: str
    confidence: float = 1.0


class DilemmaNode(BaseModel):
    id: str
    question: str
    stance_text: str
    ts: str


class OpenLoopNode(BaseModel):
    id: str
    text: str
    kind: Literal["curiosity", "cliffhanger", "concept_gap"]
    priority_note: str = "normal"
    status: Literal["open", "revisited", "archived"] = "open"


class DigestNode(BaseModel):
    id: str
    text: str
    ts: str
    audience: Literal["parent", "teacher", "learner"] = "parent"


class SafetyEventNode(BaseModel):
    id: str
    category: str
    severity: Literal["low", "medium", "high", "critical"]
    action: Literal["monitored", "care_mode", "blocked_redirected"]
    ts: str


class PipelineFaultNode(BaseModel):
    id: str
    stage: str
    error: str
    ts: str


# ---------------------------------------------------------------------------
# Composite / API View Models
# ---------------------------------------------------------------------------

class LearnerSnapshot(BaseModel):
    learner: LearnerNode
    interests: List[Dict[str, Any]] = Field(default_factory=list)
    curiosities: List[CuriosityNode] = Field(default_factory=list)
    active_tales: List[Dict[str, Any]] = Field(default_factory=list)
    open_loops: List[OpenLoopNode] = Field(default_factory=list)
    recent_entities: List[EntityNode] = Field(default_factory=list)
    known_concepts_count: int = 0


class MindViewNode(BaseModel):
    id: str
    name: str
    domain: str = "general"
    depth: float = 0.0
    confidence: float = 0.0
    status: str = "known"


class MindViewEdge(BaseModel):
    source: str
    target: str
    type: str
    why: Optional[str] = None


class MindView(BaseModel):
    nodes: List[MindViewNode]
    edges: List[MindViewEdge]


class DecisionTrace(BaseModel):
    decision_id: str
    agent: str
    kind: str
    rationale: str
    ts: str
    chose: Optional[Dict[str, Any]] = None
    because: List[Dict[str, Any]] = Field(default_factory=list)
    made_in_turn_id: Optional[str] = None
