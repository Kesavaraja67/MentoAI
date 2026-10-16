-- Q8: decision_path
-- Given a Decision id in the CHILD graph (child_<id>), return all nodes and
-- edges that justify it: the Decision itself, its CHOSE target, and all
-- BECAUSE targets with their roles.
-- Used by GET /api/decisions/{id}/path for the Why panel highlight.
--
-- Run in the CHILD graph (child_<id>).
-- Parameters: $decision_id
--
-- Returns rows of (source_id, source_label, edge_label, target_id, target_label)
-- so the frontend can reconstruct the subgraph.

MATCH (d:Decision {id: $decision_id})
OPTIONAL MATCH (d)-[chose:CHOSE]->(chose_target)
OPTIONAL MATCH (d)-[because:BECAUSE]->(because_target)
RETURN
    d.id                    AS decision_id,
    d.kind                  AS kind,
    d.summary               AS summary,
    d.memory_used           AS memory_used,
    chose_target.id         AS chose_id,
    labels(chose_target)[0] AS chose_label,
    because_target.id       AS because_id,
    labels(because_target)[0] AS because_label,
    because.role            AS because_role
