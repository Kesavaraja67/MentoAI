"""
protocol.py — Typed schemas for MentoAI's WebSocket realtime protocol.

Documented in docs/PROTOCOL.md. Supports low-latency streaming subtitles,
sentence-level TTS triggering, barge-in, viz.events, and visual card payloads.
"""
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field


# --- Inbound Messages (Client -> Server) ---

class ClientHello(BaseModel):
    type: Literal["hello"] = "hello"
    learner_id: str
    mode: Literal["A", "B"] = "A"


class TranscriptPartial(BaseModel):
    type: Literal["transcript.partial"] = "transcript.partial"
    text: str


class TranscriptFinal(BaseModel):
    type: Literal["transcript.final"] = "transcript.final"
    text: str


class BargeInEvent(BaseModel):
    type: Literal["barge_in"] = "barge_in"
    spoken_chars: int = 0


class ClientControl(BaseModel):
    type: Literal["control"] = "control"
    action: Literal["mute", "end", "pause", "resume"]


# --- Outbound Messages (Server -> Client) ---

class StateMessage(BaseModel):
    type: Literal["state"] = "state"
    state: Literal["listening", "thinking", "speaking"]


class SubtitlePerson(BaseModel):
    type: Literal["subtitle.person"] = "subtitle.person"
    text: str
    final: bool = True


class SubtitleMentoAI(BaseModel):
    type: Literal["subtitle.mentoai"] = "subtitle.mentoai"
    delta: str
    sentence_id: str


class TtsTextMessage(BaseModel):
    type: Literal["tts.text"] = "tts.text"
    sentence_id: str
    text: str


class VizEventMessage(BaseModel):
    type: Literal["viz.event"] = "viz.event"
    op: Literal["add_node", "add_edge", "pulse", "trace", "mind_refresh"]
    payload: Dict[str, Any]


class VisualCardMessage(BaseModel):
    type: Literal["visual"] = "visual"
    id: str
    kind: Literal["svg", "mermaid", "concept_map", "story_card", "number_line", "timeline"]
    payload: Dict[str, Any]


class DecisionPointerMessage(BaseModel):
    type: Literal["decision"] = "decision"
    id: str
    summary: str


class ErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    code: str
    message: str
    recoverable: bool = True
