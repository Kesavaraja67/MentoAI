"""
websocket.py — Live voice-first WebSocket endpoint for MentoAI conversations.

Handles bidirectional streaming events, concurrent Triage & Context Assembly,
sentence-level subtitle and TTS chunking, barge-in truncation, and async cold-path coordination.
"""
import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agents.triage import TriageAgent
from app.agents.companion import CompanionAgent
from app.agents.coordinator import ColdPathCoordinator
from app.agents.reflector import ReflectorAgent
from app.api.chunker import SentenceChunker
from app.graph.client import get_graph
from app.graph.queries import get_learner_snapshot, get_semantic_recall
from app.graph.embeddings import get_embedding

logger = logging.getLogger("mentoai.websocket")
router = APIRouter()

# Global state for Graph Off toggle (Rule 3 Proof)
GRAPH_MODE_ENABLED = True


def is_graph_enabled() -> bool:
    global GRAPH_MODE_ENABLED
    return GRAPH_MODE_ENABLED


def set_graph_mode(enabled: bool):
    global GRAPH_MODE_ENABLED
    GRAPH_MODE_ENABLED = enabled


@router.websocket("/ws/conversations/{conversation_id}")
async def websocket_conversation(websocket: WebSocket, conversation_id: str):
    await websocket.accept()

    learner_id = "default_learner"
    graph_name = f"learner_{learner_id}"
    recent_turns: list[dict] = []
    current_speech_task: Optional[asyncio.Task] = None
    interrupted = False

    triage_agent = TriageAgent()
    companion_agent = CompanionAgent()
    coordinator = ColdPathCoordinator()
    reflector_agent = ReflectorAgent()

    async def send_json(msg: dict):
        try:
            await websocket.send_text(json.dumps(msg))
        except Exception:
            pass

    async def emit_viz_event(event: dict):
        """Callback passed to ColdPathCoordinator to broadcast graph updates."""
        await send_json({"type": "viz.event", **event})

    try:
        # Initial greeting & state
        await send_json({"type": "state", "state": "listening"})

        while True:
            raw_text = await websocket.receive_text()
            data = json.loads(raw_text)
            msg_type = data.get("type", "")

            # 1. Hello message
            if msg_type == "hello":
                learner_id = data.get("learner_id", learner_id)
                graph_name = f"learner_{learner_id}"
                # Send initial graph snapshot if graph enabled
                if is_graph_enabled():
                    try:
                        snap = get_learner_snapshot(graph_name, learner_id)
                        if snap:
                            await send_json({
                                "type": "viz.event",
                                "op": "mind_refresh",
                                "payload": snap.model_dump(),
                            })
                    except Exception as e:
                        logger.warning(f"Failed to fetch initial snapshot: {e}")
                continue

            # 2. Barge-in interruption
            if msg_type == "barge_in":
                interrupted = True
                if current_speech_task and not current_speech_task.done():
                    current_speech_task.cancel()
                await send_json({"type": "state", "state": "listening"})
                continue

            # 3. Partial transcript (user speaking live)
            if msg_type == "transcript.partial":
                text = data.get("text", "")
                await send_json({"type": "subtitle.person", "text": text, "final": False})
                continue

            # 4. Final transcript (user finished turn)
            if msg_type == "transcript.final":
                user_text = data.get("text", "").strip()
                if not user_text:
                    continue

                interrupted = False
                await send_json({"type": "subtitle.person", "text": user_text, "final": True})
                await send_json({"type": "state", "state": "thinking"})

                turn_id = f"turn_{uuid.uuid4().hex[:8]}"
                recent_turns.append({"role": "person", "text": user_text})

                # Write user turn to graph if enabled
                if is_graph_enabled():
                    try:
                        graph = get_graph(graph_name)
                        graph.query(
                            """
                            MATCH (c:Conversation {id: $cid})
                            CREATE (t:Turn {
                                id: $tid,
                                role: 'person',
                                text: $text,
                                ts: timestamp()
                            })
                            CREATE (c)-[:HAS_TURN]->(t)
                            """,
                            {"cid": conversation_id, "tid": turn_id, "text": user_text},
                        )
                    except Exception as e:
                        logger.warning(f"Error persisting user turn: {e}")

                # Concurrently run Triage + Context Assembly
                context_pack = {"snapshot": None, "plan": None, "recall": []}
                triage_task = asyncio.create_task(asyncio.to_thread(triage_agent.evaluate, user_text))

                async def assemble_context():
                    if not is_graph_enabled():
                        return {"snapshot": None, "plan": None, "recall": []}
                    snap = None
                    recall = []
                    try:
                        snap = get_learner_snapshot(graph_name, learner_id)
                        recall = get_semantic_recall(graph_name, user_text, top_k=3)
                    except Exception as ex:
                        logger.warning(f"Context assembly lookup fault: {ex}")
                    return {"snapshot": snap, "plan": None, "recall": recall}

                context_task = asyncio.create_task(assemble_context())
                triage_res, context_pack = await asyncio.gather(triage_task, context_task)

                # Companion response generation
                await send_json({"type": "state", "state": "speaking"})

                assistant_turn_id = f"turn_{uuid.uuid4().hex[:8]}"

                async def stream_and_speak():
                    nonlocal assistant_turn_id
                    reply_text, visuals, dec_record = await asyncio.to_thread(
                        companion_agent.generate_reply,
                        graph_name=graph_name,
                        learner_id=learner_id,
                        turn_id=assistant_turn_id,
                        utterance=user_text,
                        context_pack=context_pack,
                        recent_turns=recent_turns,
                        mode=triage_res.mode,
                        safe_response=triage_res.safe_response,
                    )

                    recent_turns.append({"role": "mentoai", "text": reply_text})

                    # Stream sentences via chunker
                    chunker = SentenceChunker()
                    words = reply_text.split(" ")
                    for w in words:
                        if interrupted:
                            break
                        for sent_id, complete_sent in chunker.feed(w + " "):
                            await send_json({
                                "type": "subtitle.mentoai",
                                "delta": complete_sent,
                                "sentence_id": sent_id,
                            })
                            await send_json({
                                "type": "tts.text",
                                "sentence_id": sent_id,
                                "text": complete_sent,
                            })
                            await asyncio.sleep(0.04)

                    for sent_id, complete_sent in chunker.flush():
                        if not interrupted:
                            await send_json({
                                "type": "subtitle.mentoai",
                                "delta": complete_sent,
                                "sentence_id": sent_id,
                            })
                            await send_json({
                                "type": "tts.text",
                                "sentence_id": sent_id,
                                "text": complete_sent,
                            })

                    # Send any visual cards
                    for v in visuals:
                        await send_json({"type": "visual", **v})

                    # Send decision trace pointer
                    if dec_record and is_graph_enabled():
                        await send_json({
                            "type": "decision",
                            "id": assistant_turn_id,
                            "summary": f"{dec_record.get('chosen_move', 'dialogue')}: {dec_record.get('rationale', '')}",
                        })

                    # Write MentoAI turn to graph
                    if is_graph_enabled():
                        try:
                            graph = get_graph(graph_name)
                            graph.query(
                                """
                                MATCH (c:Conversation {id: $cid})
                                CREATE (t:Turn {
                                    id: $tid,
                                    role: 'mentoai',
                                    text: $text,
                                    ts: timestamp()
                                })
                                CREATE (c)-[:HAS_TURN]->(t)
                                """,
                                {"cid": conversation_id, "tid": assistant_turn_id, "text": reply_text},
                            )
                        except Exception as e:
                            logger.warning(f"Error persisting assistant turn: {e}")

                        # Trigger Cold Path asynchronously
                        asyncio.create_task(
                            coordinator.execute_turn_pipeline(
                                graph_name=graph_name,
                                learner_id=learner_id,
                                turn_id=assistant_turn_id,
                                user_utterance=user_text,
                                assistant_reply=reply_text,
                                event_callback=emit_viz_event,
                            )
                        )

                    await send_json({"type": "state", "state": "listening"})

                current_speech_task = asyncio.create_task(stream_and_speak())
                continue

            # 5. Session end control
            if msg_type == "control" and data.get("action") == "end":
                if is_graph_enabled():
                    reflector_res = reflector_agent.consolidate_session(
                        graph_name=graph_name,
                        learner_id=learner_id,
                        conversation_id=conversation_id,
                        turns=recent_turns,
                    )
                    await send_json({
                        "type": "viz.event",
                        "op": "trace",
                        "payload": {"status": "session_consolidated", "summary": reflector_res.summary},
                    })
                await send_json({"type": "state", "state": "listening"})
                continue

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from conversation {conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error in {conversation_id}: {e}", exc_info=True)
        await send_json({"type": "error", "code": "internal_fault", "message": str(e), "recoverable": True})
