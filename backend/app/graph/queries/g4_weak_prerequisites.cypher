// G4: weak_prerequisites
// Upstream prerequisite traversal (1 to 5 hops) returning prerequisites
// with thin evidence, low confidence (< 0.6), or an active misconception.

MATCH (target:Concept {key: $concept_key})
MATCH path = (p:Concept)-[:PREREQUISITE_OF*1..5]->(target)
MATCH (l:Learner {id: $learner_id})
OPTIONAL MATCH (l)-[k:KNOWS]->(p)
OPTIONAL MATCH (l)-[:HOLDS]->(m:Misconception {status: 'open'})-[:ABOUT]->(p)
WITH p, path, k, m,
     COALESCE(k.confidence, 0.0) AS confidence,
     CASE WHEN m IS NOT NULL THEN 1 ELSE 0 END AS has_misconception
WHERE confidence < 0.6 OR has_misconception = 1
RETURN
    p.key                                        AS prerequisite_key,
    p.name                                       AS prerequisite_name,
    p.summary                                    AS summary,
    confidence                                   AS confidence,
    has_misconception                            AS has_misconception,
    m.statement                                  AS misconception_statement,
    length(path)                                 AS hops,
    [n IN nodes(path) | COALESCE(n.name, n.key)] AS path_keys
ORDER BY has_misconception DESC, confidence ASC, hops ASC
LIMIT 3;
