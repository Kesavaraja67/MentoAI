"""
coordinator.py — Cold-path async orchestrator for MentoAI.

Connects Listener -> Cartographer -> Strategist -> Guardian in the background
after every spoken turn, emitting viz.events to active UI clients.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable

from app.agents.listener import ListenerAgent
from app.agents.cartographer import CartographerAgent
from app.agents.strategist import StrategistAgent
from app.agents.guardian import GuardianAgent
from app.graph.queries import get_mind_view

logger = logging.getLogger("mentoai.coordinator")


class ColdPathCoordinator:
    def __init__(
        self,
        listener: Optional[ListenerAgent] = None,
        cartographer: Optional[CartographerAgent] = None,
        strategist: Optional[StrategistAgent] = None,
        guardian: Optional[GuardianAgent] = None,
    ):
        self.listener = listener or ListenerAgent()
        self.cartographer = cartographer or CartographerAgent()
        self.strategist = strategist or StrategistAgent()
        self.guardian = guardian or GuardianAgent()

    async def execute_turn_pipeline(
        self,
        graph_name: str,
        learner_id: str,
        turn_id: str,
        user_utterance: str,
        assistant_reply: str,
        event_callback: Optional[Callable[[Dict[str, Any]], Any]] = None,
    ):
        """
        Executes cold path stages asynchronously:
        1. Listener: extracts evidence & curiosities, writes to FalkorDB (G8)
        2. Cartographer: maps any new candidate concepts (G9)
        3. Strategist: plans next pedagogical move & writes Decision with BECAUSE edges (G10)
        4. Guardian: audits turn for child safety and PII
        5. Emits viz.events so the UI updates real-time
        """
        try:
            logger.info(f"Cold path started for turn {turn_id}")

            # 1. Listener
            listener_res = self.listener.process_turn(
                graph_name=graph_name,
                learner_id=learner_id,
                turn_id=turn_id,
                user_utterance=user_utterance,
                assistant_reply=assistant_reply,
            )

            if event_callback and listener_res.evidence:
                await event_callback({
                    "op": "pulse",
                    "payload": {
                        "concept": listener_res.evidence[0].concept_key,
                        "verdict": listener_res.evidence[0].verdict,
                        "strength": listener_res.evidence[0].strength,
                    },
                })

            # 2. Cartographer (if concepts discovered or needed)
            candidate_keys = [ev.concept_key for ev in listener_res.evidence]
            if candidate_keys:
                carto_res = self.cartographer.expand_concepts(
                    graph_name=graph_name,
                    candidate_concepts=candidate_keys,
                    context_hint=user_utterance,
                )
                if event_callback and (carto_res.concepts or carto_res.relationships):
                    for c in carto_res.concepts:
                        await event_callback({
                            "op": "add_node",
                            "payload": {"key": c.key, "name": c.name, "summary": c.summary},
                        })

            # 3. Strategist
            recent_concept = candidate_keys[0] if candidate_keys else None
            strat_res = self.strategist.plan_next_turn(
                graph_name=graph_name,
                learner_id=learner_id,
                turn_id=turn_id,
                recent_concept=recent_concept,
            )

            if event_callback:
                await event_callback({
                    "op": "trace",
                    "payload": {
                        "move": strat_res.decision.chosen_move,
                        "rationale": strat_res.decision.rationale,
                    },
                })

            # 4. Guardian (safety check)
            self.guardian.audit_turn(
                graph_name=graph_name,
                learner_id=learner_id,
                turn_id=turn_id,
                user_text=user_utterance,
                assistant_text=assistant_reply,
            )

            # 5. Broadcast refreshed Mind constellation snapshot
            if event_callback:
                mind = get_mind_view(graph_name, limit=25)
                await event_callback({
                    "op": "mind_refresh",
                    "payload": mind.model_dump(),
                })

            logger.info(f"Cold path finished successfully for turn {turn_id}")

        except Exception as e:
            logger.error(f"Cold path pipeline encountered error on turn {turn_id}: {e}", exc_info=True)
