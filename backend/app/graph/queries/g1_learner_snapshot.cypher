// G1: learner_snapshot
// Fetches the Learner profile, register, active interests, open curiosities,
// active sagas, open loops, and recent entities for Context Assembly.

MATCH (l:Learner {id: $learner_id})
OPTIONAL MATCH (l)-[lo:LOVES]->(i:Interest)
WITH l, collect(CASE WHEN i IS NOT NULL THEN {name: i.name, summary: i.summary, strength: lo.strength} END) AS interests

OPTIONAL MATCH (l)-[:WONDERS]->(c:Curiosity {status: 'open'})
WITH l, interests, collect(CASE WHEN c IS NOT NULL THEN {id: c.id, text: c.text, intensity: c.intensity, status: c.status} END)[0..5] AS curiosities

OPTIONAL MATCH (l)-[:ON_JOURNEY]->(t:Tale {status: 'active'})
WITH l, interests, curiosities, collect(CASE WHEN t IS NOT NULL THEN {id: t.id, title: t.title, premise: t.premise, status: t.status} END)[0..2] AS active_tales

OPTIONAL MATCH (op:OpenLoop {status: 'open'})
WITH l, interests, curiosities, active_tales, collect(CASE WHEN op IS NOT NULL THEN {id: op.id, text: op.text, kind: op.kind, priority_note: op.priority_note} END)[0..5] AS open_loops

OPTIONAL MATCH (l)-[m:MENTIONED]->(e:Entity)
WITH l, interests, curiosities, active_tales, open_loops, collect(CASE WHEN e IS NOT NULL THEN {id: e.id, name: e.name, kind: e.kind, facts: e.facts} END)[0..6] AS recent_entities

OPTIONAL MATCH (l)-[:KNOWS]->(kc:Concept)
WITH l, interests, curiosities, active_tales, open_loops, recent_entities, count(kc) AS known_count

RETURN
    l.id             AS learner_id,
    l.display_name   AS display_name,
    l.language       AS language,
    l.register_text  AS register_text,
    l.register_conf  AS register_conf,
    l.voice_pref     AS voice_pref,
    interests        AS interests,
    curiosities      AS curiosities,
    active_tales     AS active_tales,
    open_loops       AS open_loops,
    recent_entities  AS recent_entities,
    known_count      AS known_concepts_count;
