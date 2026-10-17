// G12: mind_view
// Retrieves active constellation subgraph of concepts and connecting relationships
// for the real-time force-directed canvas.

MATCH (c:Concept)
OPTIONAL MATCH (l:Learner)-[k:KNOWS]->(c)
OPTIONAL MATCH (c)-[r:PREREQUISITE_OF|ANALOGOUS_TO|PART_OF]->(target:Concept)
RETURN
    c.key                           AS id,
    c.name                          AS name,
    c.domain                        AS domain,
    COALESCE(k.depth, 0.0)          AS depth,
    COALESCE(k.confidence, 0.0)     AS confidence,
    collect(DISTINCT {
        target: target.key,
        type: type(r),
        why: COALESCE(r.why, '')
    })                              AS edges
LIMIT $limit;
