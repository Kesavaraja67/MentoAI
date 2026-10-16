"""
graph/consolidate.py — Session consolidation.

At the end of a session this module:
  1. Reads all Turns and working Skill confidences from session_<id>.
  2. Writes confidences back to child_<id> Skills; updates attempts & last_seen.
  3. Creates an Episode node; links PRACTICED, EXHIBITED, USED_STYLE edges.
  4. Copies Decision nodes and their BECAUSE / CHOSE edges into the child graph.
  5. Optionally calls the LLM for a 2–3 sentence episode summary (with fallback).
  6. Deletes session_<id>.
  7. Returns a memory diff for the UI.

Idempotency: if an Episode with the same session_id already exists in the
child graph, steps 3–4 are skipped and the existing diff is returned.
The session graph is NOT deleted on error.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from collections import defaultdict

from app.graph.client import get_graph, delete_graph
from app.graph.queries import q7_get_session_turns


def consolidate(session_id: str, llm_summary_fn=None) -> dict:
    """
    Consolidate session_<session_id> into child_<child_id>.
    Returns a memory diff dict:
    {
        skills: [{id, name, before, after}],
        episode_id: str,
        hint_style_changes: [{id, before, after}],
        summary: str,
    }
    Raises on fatal error without deleting the session graph.
    """
    sess_g = get_graph(f"session_{session_id}")

    # ── Read session metadata ─────────────────────────────────────────────────
    meta_result = sess_g.query(
        """
        MATCH (s:Session {id: $sid})
        RETURN s.child_id, s.graph_mode, s.started_at
        """,
        {"sid": session_id},
    )
    if not meta_result.result_set:
        raise ValueError(f"Session {session_id} not found in graph")

    child_id, graph_mode, started_at = meta_result.result_set[0]

    # Graph-off sessions: nothing to consolidate
    if graph_mode == "off":
        delete_graph(f"session_{session_id}")
        return {
            "skills": [],
            "episode_id": "",
            "hint_style_changes": [],
            "summary": "Session ran with graph disabled.",
        }

    child_g = get_graph(f"child_{child_id}")

    # ── Idempotency check ────────────────────────────────────────────────────
    ep_check = child_g.query(
        "MATCH (e:Episode {session_id: $sid}) RETURN e.id",
        {"sid": session_id},
    )
    existing_episode_id = ep_check.result_set[0][0] if ep_check.result_set else None
    if existing_episode_id:
        # Already consolidated — return the existing diff (simplified)
        return _read_existing_diff(child_g, existing_episode_id)

    # ── Step 1: Read turns ───────────────────────────────────────────────────
    turns = q7_get_session_turns(sess_g, session_id)
    # Filter out rows with null turn_n (Session row with no turns)
    turns = [t for t in turns if t["turn_n"] is not None]

    # ── Step 2: Read working skill confidences from session ──────────────────
    skill_conf_result = sess_g.query(
        "MATCH (s:Skill) RETURN s.id, s.confidence, s.attempts, s.last_seen"
    )
    session_skills = {
        r[0]: {"confidence": r[1], "attempts": r[2], "last_seen": r[3]}
        for r in skill_conf_result.result_set
    }

    # Read BEFORE values from the child graph
    before_conf = {}
    skill_name_map = {}
    child_skill_result = child_g.query(
        "MATCH (s:Skill) RETURN s.id, s.name, s.confidence"
    )
    for r in child_skill_result.result_set:
        before_conf[r[0]] = r[2]
        skill_name_map[r[0]] = r[1]

    # ── Step 3: Write confidences back to child graph ────────────────────────
    now_str = _now()
    for skill_id, data in session_skills.items():
        child_g.query(
            """
            MATCH (s:Skill {id: $sid})
            SET s.confidence = $conf,
                s.attempts   = $attempts,
                s.last_seen  = $last_seen
            """,
            {
                "sid":       skill_id,
                "conf":      data["confidence"],
                "attempts":  data["attempts"],
                "last_seen": now_str,
            },
        )

    # ── Step 4: Compute episode stats ─────────────────────────────────────────
    correct_count = sum(1 for t in turns if t["correct"])
    total_count   = len(turns)
    hints_used    = sum(1 for t in turns if t["hint_level"] > 0)

    # Misconceptions exhibited: count by misconception_id
    misconception_counts: dict[str, int] = defaultdict(int)
    for t in turns:
        mid = t.get("misconception_id") or ""
        if mid and mid != "unclassified":
            misconception_counts[mid] += 1

    # Skills practiced: just the ones that had at least one turn
    practiced_skills = {t["skill_id"] for t in turns if t["skill_id"]}

    # ── Step 5: Hint-style learning ───────────────────────────────────────────
    # For each wrong turn followed by a hint of style S and then a correct turn
    # on the same problem: helped = 1, otherwise 0.
    style_stats: dict[str, dict] = defaultdict(lambda: {"tries": 0, "helped": 0})

    for i, t in enumerate(turns):
        if not t["correct"] and t["hint_level"] > 0 and t["hint_style"]:
            style = t["hint_style"]
            style_stats[style]["tries"] += 1
            # Check if next turn on same problem is correct
            if i + 1 < len(turns):
                next_t = turns[i + 1]
                if next_t["problem_id"] == t["problem_id"] and next_t["correct"]:
                    style_stats[style]["helped"] += 1

    # Read current style scores
    hint_before: dict[str, float] = {}
    hs_result = child_g.query(
        "MATCH (h:HintStyle) RETURN h.id, h.score, h.tries"
    )
    for r in hs_result.result_set:
        hint_before[r[0]] = r[1]

    # Update style scores
    hint_after: dict[str, float] = {}
    for style_id, stats in style_stats.items():
        if stats["tries"] == 0:
            continue
        helped_rate = stats["helped"] / stats["tries"]
        old_score   = hint_before.get(style_id, 0.5)
        new_score   = round(0.7 * old_score + 0.3 * helped_rate, 4)
        hint_after[style_id] = new_score

        child_g.query(
            """
            MATCH (h:HintStyle {id: $hid})
            SET h.score = $score,
                h.tries = h.tries + $tries
            """,
            {"hid": style_id, "score": new_score, "tries": stats["tries"]},
        )

        # Also update session graph so q4 can still be called
        sess_g.query(
            """
            MATCH (h:HintStyle {id: $hid})
            SET h.score = $score
            """,
            {"hid": style_id, "score": new_score},
        )

    # ── Step 6: LLM episode summary (with fallback) ────────────────────────
    summary = _generate_summary(
        child_id, correct_count, total_count, hints_used,
        list(practiced_skills), llm_summary_fn,
    )

    # ── Step 7: Create Episode node ────────────────────────────────────────────
    episode_id = str(uuid.uuid4())
    child_g.query(
        """
        CREATE (:Episode {
            id:         $eid,
            ts:         $ts,
            session_id: $sid,
            correct:    $correct,
            total:      $total,
            hints_used: $hints,
            summary:    $summary
        })
        """,
        {
            "eid":     episode_id,
            "ts":      now_str,
            "sid":     session_id,
            "correct": correct_count,
            "total":   total_count,
            "hints":   hints_used,
            "summary": summary,
        },
    )

    # Child -[:HAD]-> Episode
    child_g.query(
        """
        MATCH (c:Child {id: $cid}), (e:Episode {id: $eid})
        CREATE (c)-[:HAD]->(e)
        """,
        {"cid": child_id, "eid": episode_id},
    )

    # Episode -[:PRACTICED {before, after}]-> Skill
    for skill_id in practiced_skills:
        b = before_conf.get(skill_id, 0.0)
        a = session_skills.get(skill_id, {}).get("confidence", b)
        child_g.query(
            """
            MATCH (e:Episode {id: $eid}), (s:Skill {id: $sid})
            CREATE (e)-[:PRACTICED {before: $before, after: $after}]->(s)
            """,
            {"eid": episode_id, "sid": skill_id, "before": b, "after": a},
        )

    # Episode -[:EXHIBITED {count}]-> Misconception
    for mid, count in misconception_counts.items():
        child_g.query(
            """
            MATCH (e:Episode {id: $eid}), (m:Misconception {id: $mid})
            CREATE (e)-[:EXHIBITED {count: $count}]->(m)
            """,
            {"eid": episode_id, "mid": mid, "count": count},
        )

    # Episode -[:USED_STYLE {tries, helped}]-> HintStyle
    for style_id, stats in style_stats.items():
        child_g.query(
            """
            MATCH (e:Episode {id: $eid}), (h:HintStyle {id: $hid})
            CREATE (e)-[:USED_STYLE {tries: $tries, helped: $helped}]->(h)
            """,
            {
                "eid":    episode_id,
                "hid":    style_id,
                "tries":  stats["tries"],
                "helped": stats["helped"],
            },
        )

    # ── Step 8: Copy Decision nodes from session to child graph ───────────────
    _copy_decisions(sess_g, child_g, session_id, episode_id)

    # ── Step 9: Delete session graph ──────────────────────────────────────────
    delete_graph(f"session_{session_id}")

    # ── Build diff for UI ─────────────────────────────────────────────────────
    skill_diff = []
    for skill_id, data in session_skills.items():
        b = before_conf.get(skill_id, 0.0)
        a = data["confidence"]
        if abs(a - b) > 0.001:
            skill_diff.append({
                "id":    skill_id,
                "name":  skill_name_map.get(skill_id, skill_id),
                "before": b,
                "after":  a,
            })

    style_diff = [
        {"id": sid, "before": hint_before.get(sid, 0.5), "after": after}
        for sid, after in hint_after.items()
    ]

    return {
        "skills":             skill_diff,
        "episode_id":         episode_id,
        "hint_style_changes": style_diff,
        "summary":            summary,
    }


def _copy_decisions(
    sess_g,
    child_g,
    session_id: str,
    episode_id: str,
) -> None:
    """Copy all Decision nodes and their edges from the session graph to the child graph."""
    # Read decisions
    dec_result = sess_g.query(
        """
        MATCH (d:Decision)
        WHERE d.session_id = $sid
        RETURN d.id, d.ts, d.kind, d.summary, d.memory_used
        """,
        {"sid": session_id},
    )
    for row in dec_result.result_set:
        did, dts, dkind, dsummary, dmem = row
        child_g.query(
            """
            CREATE (:Decision {
                id:          $id,
                ts:          $ts,
                kind:        $kind,
                summary:     $summary,
                memory_used: $memory_used,
                session_id:  $sid
            })
            """,
            {
                "id": did, "ts": dts, "kind": dkind,
                "summary": dsummary, "memory_used": dmem or [],
                "sid": session_id,
            },
        )

        # Copy CHOSE edges (Skill or HintStyle)
        for target_type in ("Skill", "HintStyle"):
            chose_result = sess_g.query(
                f"""
                MATCH (d:Decision {{id: $did}})-[:CHOSE]->(t:{target_type})
                RETURN t.id
                """,
                {"did": did},
            )
            for r in chose_result.result_set:
                child_g.query(
                    f"""
                    MATCH (d:Decision {{id: $did}}), (t:{target_type} {{id: $tid}})
                    CREATE (d)-[:CHOSE]->(t)
                    """,
                    {"did": did, "tid": r[0]},
                )

        # Copy BECAUSE edges (Skill, Misconception, Episode)
        # Turn references become Episode references in the child graph
        for target_type in ("Skill", "Misconception"):
            because_result = sess_g.query(
                f"""
                MATCH (d:Decision {{id: $did}})-[b:BECAUSE]->(t:{target_type})
                RETURN t.id, b.role
                """,
                {"did": did},
            )
            for r in because_result.result_set:
                child_g.query(
                    f"""
                    MATCH (d:Decision {{id: $did}}), (t:{target_type} {{id: $tid}})
                    CREATE (d)-[:BECAUSE {{role: $role}}]->(t)
                    """,
                    {"did": did, "tid": r[0], "role": r[1]},
                )

        # Turn BECAUSE → Episode BECAUSE in child graph
        turn_because = sess_g.query(
            """
            MATCH (d:Decision {id: $did})-[b:BECAUSE]->(t:Turn)
            RETURN b.role
            """,
            {"did": did},
        )
        for r in turn_because.result_set:
            child_g.query(
                """
                MATCH (d:Decision {id: $did}), (e:Episode {id: $eid})
                CREATE (d)-[:BECAUSE {role: $role}]->(e)
                """,
                {"did": did, "eid": episode_id, "role": r[0]},
            )


def _generate_summary(
    child_id: str,
    correct: int,
    total: int,
    hints: int,
    skills: list[str],
    llm_fn,
) -> str:
    """Try the LLM; fall back to a template on any failure."""
    if total == 0:
        return "The session had no problems."

    accuracy = int(100 * correct / total) if total else 0
    template = (
        f"Worked on {', '.join(skills) if skills else 'mixed skills'}. "
        f"Got {correct} of {total} right ({accuracy}%). "
        f"Used {hints} hints."
    )

    if llm_fn is None:
        return template

    try:
        result = llm_fn(
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Write a 2-to-3 sentence plain-English summary of this "
                        f"learning session for a parent. "
                        f"Child: {child_id}. Skills practiced: {', '.join(skills)}. "
                        f"Correct: {correct}/{total}. Hints used: {hints}. "
                        f"Be warm, factual, no jargon."
                    ),
                }
            ],
            max_tokens=80,
            temperature=0.4,
        )
        return result if result else template
    except Exception:
        return template


def _read_existing_diff(child_g, episode_id: str) -> dict:
    """Return a minimal diff for an already-consolidated episode."""
    ep_result = child_g.query(
        "MATCH (e:Episode {id: $eid}) RETURN e.summary",
        {"eid": episode_id},
    )
    summary = ep_result.result_set[0][0] if ep_result.result_set else ""
    return {
        "skills": [],
        "episode_id": episode_id,
        "hint_style_changes": [],
        "summary": summary,
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
