// G6: open_loops_ranked
// Returns open curiosities, saga cliffhangers, and concepts worth revisiting.

MATCH (op:OpenLoop {status: 'open'})
OPTIONAL MATCH (op)-[:ABOUT]->(related)
RETURN
    op.id                                       AS loop_id,
    op.text                                     AS text,
    op.kind                                     AS kind,
    op.priority_note                            AS priority_note,
    labels(related)[0]                          AS related_type,
    COALESCE(related.name, related.title, '')   AS related_name,
    COALESCE(related.key, related.id, '')       AS related_id
ORDER BY
    CASE WHEN op.priority_note = 'high' THEN 1 ELSE 2 END ASC
LIMIT 5;
