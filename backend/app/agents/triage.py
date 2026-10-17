"""
triage.py — Fast Safety Gate for MentoAI turns.

Classifies incoming speech into normal, care, or refuse_redirect modes
before the Companion generates speech.
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.agents.runtime import AgentRuntime
from app.agents.safety import (
    classify_safety_keywords,
    SAFETY_CARE_MESSAGE,
    SAFETY_REFUSE_MESSAGE,
)

PROMPT_PATH = Path(__file__).parent / "prompts" / "triage.md"


class TriageResult(BaseModel):
    mode: str = Field(..., description="normal | care | refuse_redirect")
    categories: List[str] = Field(default_factory=list)
    redirect_topic: Optional[str] = None
    explanation: str = Field(default="")
    safe_response: Optional[str] = None


class TriageAgent:
    def __init__(self, runtime: Optional[AgentRuntime] = None):
        self.runtime = runtime or AgentRuntime()
        self.prompt_text = (
            PROMPT_PATH.read_text(encoding="utf-8")
            if PROMPT_PATH.exists()
            else "You are the Triage Safety Guard for MentoAI."
        )

    def evaluate(self, utterance: str) -> TriageResult:
        """
        Fast multi-stage evaluation:
        1. Fast deterministic keyword / constitutional check
        2. Model-based structured classification
        """
        # Step 1: Instant deterministic constitutional safety check
        quick_mode, reason = classify_safety_keywords(utterance)
        if quick_mode == "care":
            return TriageResult(
                mode="care",
                categories=["distress_emergency"],
                explanation=reason,
                safe_response=SAFETY_CARE_MESSAGE,
            )
        if quick_mode == "refuse_redirect":
            return TriageResult(
                mode="refuse_redirect",
                categories=["policy_violation"],
                redirect_topic="safe science exploration",
                explanation=reason,
                safe_response=SAFETY_REFUSE_MESSAGE,
            )

        # Step 2: Model evaluation for nuanced classification
        try:
            res = self.runtime.call_structured(
                system_prompt=self.prompt_text,
                user_prompt=f"User utterance: \"{utterance}\"",
                expected_schema=TriageResult,
                tier="fast",
            )
            mode = res.get("mode", "normal")
            safe_resp = None
            if mode == "care":
                safe_resp = SAFETY_CARE_MESSAGE
            elif mode == "refuse_redirect":
                safe_resp = SAFETY_REFUSE_MESSAGE
            return TriageResult(
                mode=mode,
                categories=res.get("categories", []),
                redirect_topic=res.get("redirect_topic"),
                explanation=res.get("explanation", res.get("reason", "")),
                safe_response=safe_resp,
            )
        except Exception:
            # Safe fail-open for normal educational queries
            return TriageResult(
                mode="normal",
                categories=["fallback"],
                explanation="Defaulted to normal on parse fault",
            )
