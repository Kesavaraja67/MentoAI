// G7: saga_state
// Retrieves active saga state, latest chapter cliffhanger, featured entities,
// and taught concepts for continuing ongoing stories.

MATCH (t:Tale {status: 'active'})
OPTIONAL MATCH (t)-[:HAS_CHAPTER]->(ch:Chapter)
WITH t, ch ORDER BY ch.idx DESC
WITH t, collect(ch)[0] AS last_chapter
OPTIONAL MATCH (t)-[:FEATURES]->(feat)
OPTIONAL MATCH (t)-[:TEACHES]->(conc:Concept)
RETURN
    t.id                               AS tale_id,
    t.title                            AS title,
    t.premise                          AS premise,
    last_chapter.idx                   AS last_chapter_idx,
    last_chapter.text                  AS last_chapter_text,
    last_chapter.cliffhanger           AS cliffhanger,
    collect(DISTINCT feat.name)        AS featured_entities,
    collect(DISTINCT conc.name)        AS taught_concepts
LIMIT 1;
