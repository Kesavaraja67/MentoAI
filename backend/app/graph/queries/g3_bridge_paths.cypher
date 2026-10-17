// G3: bridge_paths
// Finds shortest connection paths from target concept to concepts the learner
// already KNOWS or LOVES through interests.

MATCH (target:Concept {key: $target_concept_key})
MATCH (l:Learner {id: $learner_id})
MATCH path = (target)-[:PREREQUISITE_OF|ANALOGOUS_TO|PART_OF|TOUCHES*1..3]-(anchor)
WHERE (l)-[:KNOWS]->(anchor:Concept) OR (l)-[:LOVES]->(anchor:Interest)
RETURN
    anchor.name                                         AS anchor_name,
    labels(anchor)[0]                                   AS anchor_type,
    length(path)                                        AS hops,
    [n IN nodes(path) | COALESCE(n.name, n.key)]        AS path_names,
    [r IN relationships(path) | type(r)]                AS path_relationships
ORDER BY hops ASC
LIMIT 3;
