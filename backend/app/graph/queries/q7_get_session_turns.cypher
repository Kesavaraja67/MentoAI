-- Q7: get_session_turns
-- Read all Turns from a session in order, plus the Session node metadata.
-- Used by the Consolidator (graph/consolidate.py) to compute the memory diff.
--
-- Run in the SESSION graph (session_<id>).
-- Parameters: $session_id
--
-- Returns one row per Turn, plus session metadata repeated.

MATCH (sess:Session {id: $session_id})
OPTIONAL MATCH (sess)-[:HAS_TURN]->(t:Turn)
RETURN
    sess.child_id       AS child_id,
    sess.started_at     AS started_at,
    sess.graph_mode     AS graph_mode,
    t.n                 AS turn_n,
    t.problem_id        AS problem_id,
    t.skill_id          AS skill_id,
    t.op                AS op,
    t.a                 AS a,
    t.b                 AS b,
    t.answer            AS answer,
    t.given             AS given,
    t.correct           AS correct,
    t.misconception_id  AS misconception_id,
    t.hint_level        AS hint_level,
    t.hint_style        AS hint_style,
    t.ts                AS ts
ORDER BY t.n ASC
