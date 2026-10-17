// G5: style_outcomes
// Aggregates pedagogical TeachingMove outcomes for this learner to learn
// which teaching styles are most effective.

MATCH (m:TeachingMove)<-[:USED]-(d:Decision)-[:USED]->(m)-[l:LED_TO]->(e:Evidence)
RETURN
    m.name                                                        AS move_name,
    count(l)                                                      AS times_used,
    sum(CASE WHEN l.outcome = 'success' OR e.verdict IN ['demonstrated', 'emerging'] THEN 1 ELSE 0 END) AS successes,
    avg(e.strength)                                               AS avg_strength
ORDER BY successes DESC, avg_strength DESC;
