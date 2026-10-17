// G13: merge_duplicates
// Identifies candidate duplicate concepts with overlapping names or keys
// for consolidation by the Reflector.

MATCH (c1:Concept), (c2:Concept)
WHERE c1.key < c2.key
  AND (
      toLower(c1.name) = toLower(c2.name)
      OR toLower(c1.key) = toLower(c2.key)
      OR (size(c1.name) > 4 AND toLower(c2.name) CONTAINS toLower(c1.name))
  )
RETURN
    c1.key   AS key1,
    c1.name  AS name1,
    c2.key   AS key2,
    c2.name  AS name2
LIMIT 5;
