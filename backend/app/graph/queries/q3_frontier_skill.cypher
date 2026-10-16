-- Q3: frontier_skill
-- Find the next skill to work on: the skill with the lowest confidence
-- among skills whose ALL prerequisites are mastered (confidence >= 0.8).
-- "Frontier" = ready to learn but not yet mastered.
--
-- FalkorDB note: NOT EXISTS { subquery } is not supported.
-- Instead: OPTIONAL MATCH the prerequisite that is NOT mastered.
-- If no such prerequisite exists (optional_prereq IS NULL), all prereqs are mastered.
--
-- Run in the SESSION graph (session_<id>).
-- No parameters.
--
-- Returns: skill_id, skill_name, confidence

MATCH (s:Skill)
WHERE s.confidence < 0.8
OPTIONAL MATCH (unmet:Skill)-[:PREREQUISITE_OF]->(s)
WHERE unmet.confidence < 0.8
WITH s, unmet
WHERE unmet IS NULL
RETURN
    s.id         AS skill_id,
    s.name       AS skill_name,
    s.confidence AS confidence
ORDER BY s.order ASC, s.confidence ASC
LIMIT 1
