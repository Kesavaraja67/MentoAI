-- Q1: get_child_summary
-- Returns the Child node plus their skills (with confidence) and interests.
-- Used by GET /api/children and by the Planner to build context.
-- Parameters: $child_id (string)

MATCH (c:Child {id: $child_id})
OPTIONAL MATCH (c)-[:INTERESTED_IN]->(i:Interest)
OPTIONAL MATCH (s:Skill)
WHERE s.confidence > 0
RETURN
    c.id        AS child_id,
    c.name      AS name,
    c.age       AS age,
    collect(DISTINCT i.name)                        AS interests,
    collect(DISTINCT {id: s.id, name: s.name, confidence: s.confidence})
                                                    AS skills
