// G14: hubs_and_clusters
// Identifies high-degree concept hubs to map the learner's major interest worlds
// and knowledge clusters for the Grown-Up Digest.

MATCH (c:Concept)
OPTIONAL MATCH (c)-[r:PREREQUISITE_OF|ANALOGOUS_TO|PART_OF|TOUCHES]-(other)
WITH c, count(r) AS degree
ORDER BY degree DESC
LIMIT 8
RETURN
    c.key     AS key,
    c.name    AS name,
    c.domain  AS domain,
    degree    AS degree;
