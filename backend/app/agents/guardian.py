"""
guardian.py — Safety and child-protection auditor for MentoAI.

Audits every conversational turn asynchronously to verify constitutional
compliance, detects PII for graph redaction, and logs SafetyEvent nodes.
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.agents.runtime import AgentRuntime
from app.graph.client import get_graph

logger = logging.getLogger("mentoai.guardian")
PROMPT_PATH = Path(__file__).parent / "prompts" / "guardian.md"


class GuardianAuditResult(BaseModel):
    safety_score: float = 1.0
    flagged: bool = False
    severity: str = "none"
    category: str = "none"
    pii_to_redact: List[str] = Field(default_factory=list)
    notes: str = ""


class GuardianAgent:
    def __init__(self, runtime: Optional[AgentRuntime] = None):
        self.runtime = runtime or AgentRuntime()
        self.prompt_text = (
            PROMPT_PATH.read_text(encoding="utf-8")
            if PROMPT_PATH.exists()
            else "You are the Guardian Auditor for MentoAI."
        )

    def audit_turn(
        self,
        graph_name: str,
        learner_id: str,
        turn_id: str,
        user_text: str,
        assistant_text: str,
    ) -> GuardianAuditResult:
        """
        Audits turn for PII and safety violations. Logs SafetyEvent node if flagged.
        """
        prompt = f"""
Audit Turn:
User: "{user_text}"
Assistant: "{assistant_text}"

Check strictly for PII disclosures, inappropriate content, or distress.
"""
        raw_res = self.runtime.call_structured(
            system_prompt=self.prompt_text,
            user_prompt=prompt,
            expected_schema=GuardianAuditResult,
            tier="fast",
        )

        result = GuardianAuditResult(**raw_res)

        if result.flagged:
            try:
                graph = get_graph(graph_name)
                graph.query(
                    """
                    MATCH (l:Learner {id: $lid})
                    CREATE (s:SafetyEvent {
                        id: randomUUID(),
                        category: $category,
                        severity: $severity,
                        action: 'flagged_for_review',
                        notes: $notes,
                        ts: timestamp()
                    })
                    CREATE (l)-[:SAFETY_FLAG]->(s)
                    """,
                    {
                        "lid": learner_id,
                        "category": result.category,
                        "severity": result.severity,
                        "notes": result.notes,
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to record safety event in graph: {e}")

        return result
