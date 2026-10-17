// G9: write_concept_neighbourhood
// Upserts a concept node idempotently by key, setting summary and domain.

MERGE (c:Concept {key: $key})
ON CREATE SET
    c.name = $name,
    c.summary = $summary,
    c.domain = $domain,
    c.created_by = $created_by,
    c.created_at = $created_at
ON MATCH SET
    c.name = $name,
    c.summary = $summary,
    c.domain = $domain
RETURN c.key AS key, c.name AS name;
