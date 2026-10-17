// G10: write_decision
// Records an agent decision node with explicit rationale and timestamp.

CREATE (d:Decision {
    id: $decision_id,
    agent: $agent,
    kind: $kind,
    rationale: $rationale,
    confidence: $confidence,
    ts: $ts,
    turn_id: $turn_id
})
WITH d
OPTIONAL MATCH (t:Turn {id: $turn_id})
FOREACH (_ IN CASE WHEN t IS NOT NULL THEN [1] ELSE [] END |
    CREATE (d)-[:MADE_IN]->(t)
)
RETURN d.id AS decision_id;
