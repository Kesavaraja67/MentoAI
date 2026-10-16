"""
models.py — shared Pydantic request/response models for the Primer API.

Keep this file flat and readable. Judges and the human reviewer read this
to understand the API surface. No clever inheritance chains.
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


# ── Children ────────────────────────────────────────────────────────────────

class ChildSummary(BaseModel):
    id: str
    name: str
    age: int
    interests: list[str]
    # Skills at a glance: just the ones with confidence > 0
    skills: list[dict]  # [{id, name, confidence}]


# ── Sessions ─────────────────────────────────────────────────────────────────

class StartSessionRequest(BaseModel):
    child_id: str
    graph_mode: Literal["on", "off"] = "on"


class ProblemOut(BaseModel):
    problem_id: str
    skill_id: str
    op: Literal["+", "-", "?"]
    a: int
    b: int
    answer: int
    story_slots: dict  # used by the frontend to render the story frame


class StartSessionResponse(BaseModel):
    session_id: str
    problem: ProblemOut
    story: str  # 1–2 sentence story frame (from LLM or template)


class AnswerRequest(BaseModel):
    problem_id: str
    given: int
    free_text: Optional[str] = None  # reflective response after correct answer


class AnswerResponse(BaseModel):
    correct: bool
    kind: Literal["praise", "hint", "regress", "advance", "return"]
    tutor_text: str
    next_problem: Optional[ProblemOut] = None
    decision_ids: list[str] = Field(default_factory=list)
    working_confidence: float  # current session confidence for the active skill


class EndSessionResponse(BaseModel):
    """Memory diff returned after consolidation."""
    skills: list[dict]   # [{id, name, before, after}]
    episode_id: str
    hint_style_changes: list[dict]  # [{id, before, after}]
    summary: str         # plain-English episode summary


# ── Graph views ──────────────────────────────────────────────────────────────

class GraphNode(BaseModel):
    id: str
    label: str
    kind: str   # Skill | Misconception | HintStyle | Decision | Episode | Interest | Turn | Session
    properties: dict = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    label: str
    properties: dict = Field(default_factory=dict)


class GraphView(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


# ── Decisions ────────────────────────────────────────────────────────────────

class DecisionOut(BaseModel):
    id: str
    ts: str
    kind: str
    summary: str
    memory_used: list[str]


# ── Demo / reset ─────────────────────────────────────────────────────────────

class ResetResponse(BaseModel):
    status: str
    personas_seeded: list[str]


# ── Error ─────────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    detail: str
