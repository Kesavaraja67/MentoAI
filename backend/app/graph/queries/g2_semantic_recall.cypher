// G2: semantic_recall
// Recalls candidate concepts, curiosities, chapters, and recent turns relevant
// to the user query, expanding 1 hop to surface connected knowledge.

MATCH (c:Concept)
WHERE toLower(c.name) CONTAINS toLower($query_text)
   OR toLower(c.summary) CONTAINS toLower($query_text)
   OR toLower(c.key) CONTAINS toLower($query_text)
OPTIONAL MATCH (c)-[r]-(neighbor:Concept)
RETURN
    c.key                      AS key,
    c.name                     AS name,
    c.summary                  AS summary,
    c.domain                   AS domain,
    labels(c)[0]               AS label,
    collect(DISTINCT {
        rel: type(r),
        neighbor_key: neighbor.key,
        neighbor_name: neighbor.name
    })[0..4]                   AS context_neighbors
LIMIT $limit;
