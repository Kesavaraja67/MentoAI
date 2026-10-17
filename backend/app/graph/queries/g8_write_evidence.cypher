// G8: write_evidence
// Records evaluated evidence from a learner's turn and updates their KNOWS edge.

MATCH (t:Turn {id: $turn_id})
MATCH (c:Concept {key: $concept_key})
MATCH (l:Learner {id: $learner_id})

CREATE (e:Evidence {
    id: $evidence_id,
    kind: $kind,
    quote: $quote,
    verdict: $verdict,
    strength: $strength,
    ts: $ts
})
CREATE (t)-[:PRODUCED]->(e)
CREATE (e)-[:ABOUT]->(c)

MERGE (l)-[k:KNOWS]->(c)
ON CREATE SET
    k.depth = $new_depth,
    k.confidence = $new_confidence,
    k.trend = 'emerging',
    k.last_evidence_ts = $ts,
    k.rationale = $rationale
ON MATCH SET
    k.depth = $new_depth,
    k.confidence = $new_confidence,
    k.trend = CASE WHEN $new_confidence >= k.confidence THEN 'improving' ELSE 'declining' END,
    k.last_evidence_ts = $ts,
    k.rationale = $rationale

RETURN e.id AS evidence_id, k.confidence AS updated_confidence;
