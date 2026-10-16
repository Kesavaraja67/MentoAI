-- Q6: write_decision
-- Record a Decision node in the session graph with CHOSE and BECAUSE edges.
--
-- Run in the SESSION graph (session_<id>).
-- Parameters:
--   $decision_id, $ts, $kind, $summary, $memory_used (list of strings),
--   $session_id
--   $chose_id       — id of the Skill or HintStyle chosen (or "")
--   $chose_label    — "Skill" or "HintStyle" (to match the right node type)
--   $because_ids    — list of {id, label, role} for BECAUSE edges
--                     label is "Skill" | "Misconception" | "Episode" | "Turn"
--
-- This query creates the Decision and its CHOSE edge.
-- BECAUSE edges are written separately in Python (one query per edge)
-- because FalkorDB does not support dynamic label matching in a single pass.

MATCH (sess:Session {id: $session_id})
CREATE (d:Decision {
    id:          $decision_id,
    ts:          $ts,
    kind:        $kind,
    summary:     $summary,
    memory_used: $memory_used,
    session_id:  $session_id
})
RETURN d.id AS decision_id
