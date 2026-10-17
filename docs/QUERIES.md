# MentoAI: FalkorDB Cypher Queries Catalog (G1–G15)

All queries are maintained as standalone `.cypher` files under `backend/app/graph/queries/` and executed via typed wrappers in `backend/app/graph/queries.py`.

---

## Catalog Overview

| ID | Query Name | Purpose | Caller Agent | Cypher File |
|---|---|---|---|---|
| **G1** | `learner_snapshot` | Fetches register, interests, active curiosities, open loops, and recent entities | Context Assembly | `g1_learner_snapshot.cypher` |
| **G2** | `semantic_recall` | 384-d Vector search over Concept embeddings + 1-hop expansion | Context Assembly / `recall` tool | `g2_semantic_recall.cypher` |
| **G3** | `bridge_paths` | Shortest paths linking target concept to things the learner KNOWS or LOVES | Strategist / `bridge` tool | `g3_bridge_paths.cypher` |
| **G4** | `weak_prerequisites` | 1-5 hop upstream traversal finding concepts with thin evidence or misconceptions | Strategist | `g4_weak_prerequisites.cypher` |
| **G5** | `style_outcomes` | Historical success rates of pedagogical moves for this learner | Strategist | `g5_style_outcomes.cypher` |
| **G6** | `open_loops_ranked` | Ranks unresolved curiosities and saga cliffhangers for session opening | Strategist / Reflector | `g6_open_loops_ranked.cypher` |
| **G7** | `saga_state` | Retrieves active Tale, current chapter cliffhanger, and featured entities | Storyteller | `g7_saga_state.cypher` |
| **G8** | `write_evidence` | Creates Evidence node, links to Turn and Concept, upserts KNOWS relation | Listener | `g8_write_evidence.cypher` |
| **G9** | `write_concept_neighbourhood` | Idempotent upsert of Concept nodes and semantic relationships | Cartographer | `g9_write_concept_neighbourhood.cypher` |
| **G10** | `write_decision` | Creates Decision with CHOSE and explicit BECAUSE provenance edges | Strategist / Companion | `g10_write_decision.cypher` |
| **G11** | `decision_trace` | Multi-hop provenance neighborhood for the Why Panel | API / UI | `g11_decision_trace.cypher` |
| **G12** | `mind_view` | Subgraph of top active concepts and typed links for Constellation visualizer | API / UI | `g12_mind_view.cypher` |
| **G13** | `merge_duplicates` | Finds candidate duplicate concepts via cosine similarity and name overlap | Reflector | `g13_merge_duplicates.cypher` |
| **G14** | `hubs_and_clusters` | Computes graph centrality and connected components | Reflector / Digest | `g14_hubs_and_clusters.cypher` |
| **G15** | `forget_learner` | Drops the tenant graph for complete privacy erasure | API (Rule 6) | `g15_forget_learner.cypher` |

---

## Detailed Cypher Examples

### G1: Learner Snapshot
```cypher
MATCH (l:Learner {id: $learner_id})
OPTIONAL MATCH (l)-[r_int:LOVES]->(i:Interest)
OPTIONAL MATCH (l)-[:WONDERS]->(c:Curiosity {status: 'open'})
OPTIONAL MATCH (l)-[:ON_JOURNEY]->(tale:Tale {status: 'active'})
OPTIONAL MATCH (l)-[:HAS_OPEN_LOOP]->(op:OpenLoop {status: 'open'})
OPTIONAL MATCH (l)-[m:MENTIONED]->(e:Entity)
OPTIONAL MATCH (l)-[:KNOWS]->(k:Concept)
RETURN
    l.id AS id,
    l.display_name AS display_name,
    l.language AS language,
    l.register_text AS register_text,
    l.register_conf AS register_conf,
    l.voice_pref AS voice_pref,
    collect(DISTINCT i.name) AS interests,
    collect(DISTINCT {id: c.id, text: c.text, intensity: c.intensity}) AS curiosities,
    collect(DISTINCT {id: tale.id, title: tale.title}) AS active_tales,
    collect(DISTINCT {id: op.id, text: op.text, priority: op.priority}) AS open_loops,
    collect(DISTINCT {name: e.name, kind: e.kind}) AS recent_entities,
    count(DISTINCT k) AS known_concepts_count
```

### G3: Bridge Paths
```cypher
MATCH (target:Concept {key: $target_concept})
MATCH (l:Learner {id: $learner_id})
MATCH (known:Concept)<-[:KNOWS]-(l)
MATCH p = shortestPath((target)-[:PREREQUISITE_OF|ANALOGOUS_TO|PART_OF|TOUCHES*1..4]-(known))
WHERE target <> known
RETURN
    known.key AS bridge_concept,
    known.name AS bridge_name,
    [rel IN relationships(p) | type(rel)] AS edge_types,
    length(p) AS hops
ORDER BY hops ASC
LIMIT 3
```

### G11: Decision Trace (The Why Panel)
```cypher
MATCH (d:Decision {id: $decision_id})
OPTIONAL MATCH (d)-[:CHOSE]->(move:TeachingMove)
OPTIONAL MATCH (d)-[:TARGETS]->(c:Concept)
OPTIONAL MATCH (d)-[:MADE_IN]->(t:Turn)
OPTIONAL MATCH (d)-[b:BECAUSE]->(reason)
RETURN
    d.id AS decision_id,
    d.agent AS agent,
    d.kind AS kind,
    d.chosen_move AS chosen_move,
    d.rationale AS rationale,
    d.confidence AS confidence,
    d.ts AS ts,
    c.name AS chosen_target,
    t.text AS turn_text,
    collect({
        type: labels(reason)[0],
        note: b.note,
        text: coalesce(reason.text, reason.quote, reason.statement, reason.name)
    }) AS because_items,
    collect(DISTINCT move.name) AS teaching_moves
```
