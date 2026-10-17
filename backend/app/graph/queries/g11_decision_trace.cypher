// G11: decision_trace
// Retrieves the provenance neighbourhood around a Decision for the Why Panel,
// showing what was chosen, the rationale, and the causal BECAUSE connections.

MATCH (d:Decision)
WHERE d.id = $decision_id OR d.turn_id = $decision_id
OPTIONAL MATCH (d)-[:CHOSE]->(c)
OPTIONAL MATCH (d)-[b:BECAUSE]->(reason)
OPTIONAL MATCH (d)-[:MADE_IN]->(t:Turn)

RETURN
    d.id                                              AS decision_id,
    d.agent                                           AS agent,
    d.kind                                            AS kind,
    d.rationale                                       AS rationale,
    d.ts                                              AS ts,
    d.confidence                                      AS confidence,
    labels(c)[0]                                      AS chose_type,
    COALESCE(c.name, c.key, c.id, '')                 AS chose_name,
    t.id                                              AS turn_id,
    collect(DISTINCT {
        type: labels(reason)[0],
        id: COALESCE(reason.id, reason.key, reason.name, ''),
        name: COALESCE(reason.name, reason.statement, reason.quote, reason.text, reason.id, ''),
        note: COALESCE(b.note, '')
    })                                                AS because_items;
