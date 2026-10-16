-- Q2: diagnose_weak_ancestor
-- Variable-length traversal: starting from a Skill node, walk PREREQUISITE_OF
-- edges backwards (upstream) up to 5 hops to find the weakest ancestor
-- (confidence < 0.5 threshold = "weak" per spec section 7.3).
-- If a misconception id is supplied, also check which skill it INDICATES_WEAK.
--
-- Run this in the SESSION graph (session_<id>).
-- Parameters: $skill_id (string), $misconception_id (string or "")
--
-- Returns: weak_skill_id, weak_skill_name, weak_confidence, path_ids (list)
-- The path_ids are the skill ids traversed, for the Decision BECAUSE edges.

-- Step 1: If we have a misconception, follow its INDICATES_WEAK edge first.
-- Step 2: From that (or from the current skill), walk PREREQUISITE_OF backwards.

OPTIONAL MATCH (m:Misconception {id: $misconception_id})-[:INDICATES_WEAK]->(indicated:Skill)
WITH indicated

MATCH path = (weak:Skill)-[:PREREQUISITE_OF*1..5]->(start:Skill {id: $skill_id})
WHERE weak.confidence < 0.5
WITH weak, path,
     CASE WHEN indicated IS NOT NULL AND indicated.id = weak.id THEN 1 ELSE 0 END AS is_indicated
ORDER BY is_indicated DESC, weak.confidence ASC, length(path) ASC
LIMIT 1

RETURN
    weak.id         AS weak_skill_id,
    weak.name       AS weak_skill_name,
    weak.confidence AS weak_confidence,
    [n IN nodes(path) | n.id] AS path_ids
