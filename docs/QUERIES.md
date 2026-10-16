# Primer: Cypher Queries Reference

This document catalogs the 8 named Cypher queries powering Primer's graph architecture.
All query definitions live exclusively as raw `.cypher` files under [`backend/app/graph/queries/`](file:///d:/projects/Nell%20Ai/primer/backend/app/graph/queries/) and are executed via typed helpers in [`backend/app/graph/queries.py`](file:///d:/projects/Nell%20Ai/primer/backend/app/graph/queries.py).

---

## Architecture Summary

| Context Graph | FalkorDB Key | Lifetime | Queries |
|---|---|---|---|
| **Curriculum Template** | `curriculum` | Seed / static template | Seeded once, cloned on demand |
| **Long-Term Memory** | `child_<child_id>` | Persistent per tenant/child | Q1, Q8, consolidation |
| **Working Memory** | `session_<session_id>` | Transient (session duration) | Q2, Q3, Q4, Q5, Q6, Q7 |

---

## Q1: `get_child_summary`
- **File:** [`q1_child_summary.cypher`](file:///d:/projects/Nell%20Ai/primer/backend/app/graph/queries/q1_child_summary.cypher)
- **Target Graph:** `child_<id>` (Long-Term Memory)
- **Parameters:** `$child_id` (string)
- **Purpose:** Fetches the `Child` profile, their current skill confidences, and their interests for context building and child selection.
- **Cypher:**
```cypher
MATCH (c:Child {id: $child_id})
OPTIONAL MATCH (c)-[:INTERESTED_IN]->(i:Interest)
WITH c, collect(i.name) AS interests
MATCH (s:Skill)
RETURN
    c.id                AS child_id,
    c.name              AS name,
    c.age               AS age,
    interests           AS interests,
    collect({
        id: s.id,
        name: s.name,
        confidence: s.confidence,
        order: s.order
    })                  AS skills
```

---

## Q2: `diagnose_weak_ancestor`
- **File:** [`q2_diagnose_weak_ancestor.cypher`](file:///d:/projects/Nell%20Ai/primer/backend/app/graph/queries/q2_diagnose_weak_ancestor.cypher)
- **Target Graph:** `session_<id>` (Working Memory)
- **Parameters:** `$skill_id` (string), `$misconception_id` (string or `""`)
- **Purpose:** Variable-length prerequisite graph traversal (1 to 5 hops upstream: `(weak)-[:PREREQUISITE_OF*1..5]->(start)`). Walks backwards through prerequisite relationships to pinpoint the root weak skill (confidence < 0.5). If a classified misconception indicates a skill (`INDICATES_WEAK`), prioritization elevates that match.
- **Cypher:**
```cypher
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
```

---

## Q3: `frontier_skill`
- **File:** [`q3_frontier_skill.cypher`](file:///d:/projects/Nell%20Ai/primer/backend/app/graph/queries/q3_frontier_skill.cypher)
- **Target Graph:** `session_<id>` (Working Memory)
- **Parameters:** None
- **Purpose:** Determines the next skill ready to learn. Identifies unmastered skills (`confidence < 0.8`) where *all* direct prerequisites are already mastered (`confidence >= 0.8`), picking the earliest in curriculum order (`s.order ASC`).
- **Cypher:**
```cypher
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
```

---

## Q4: `rank_hint_styles`
- **File:** [`q4_rank_hint_styles.cypher`](file:///d:/projects/Nell%20Ai/primer/backend/app/graph/queries/q4_rank_hint_styles.cypher)
- **Target Graph:** `session_<id>` (Working Memory)
- **Parameters:** None
- **Purpose:** Retrieves procedural memory for hint styles (`story`, `visual`, `question`, `physical`) ordered by historical effectiveness: `score DESC`, `tries ASC`, `order ASC`.
- **Cypher:**
```cypher
MATCH (h:HintStyle)
RETURN
    h.id    AS id,
    h.score AS score,
    h.tries AS tries,
    h.order AS order
ORDER BY h.score DESC, h.tries ASC, h.order ASC
```

---

## Q5: `write_turn`
- **File:** [`q5_write_turn.cypher`](file:///d:/projects/Nell%20Ai/primer/backend/app/graph/queries/q5_write_turn.cypher)
- **Target Graph:** `session_<id>` (Working Memory)
- **Parameters:** `$session_id`, `$n`, `$problem_id`, `$skill_id`, `$op`, `$a`, `$b`, `$answer`, `$given`, `$correct`, `$misconception_id`, `$hint_level`, `$hint_style`, `$ts`
- **Purpose:** Records each interaction turn as an episodic node, linked to the `Session` and chained via `[:NEXT]` edges from previous turns.
- **Cypher:**
```cypher
MATCH (s:Session {id: $session_id})
CREATE (t:Turn {
    n:                $n,
    problem_id:       $problem_id,
    skill_id:         $skill_id,
    op:               $op,
    a:                $a,
    b:                $b,
    answer:           $answer,
    given:            $given,
    correct:          $correct,
    misconception_id: $misconception_id,
    hint_level:       $hint_level,
    hint_style:       $hint_style,
    ts:               $ts
})
CREATE (s)-[:HAS_TURN]->(t)
SET s.turn_count = s.turn_count + 1
WITH s, t
OPTIONAL MATCH (s)-[:HAS_TURN]->(prev:Turn {n: $n - 1})
FOREACH (_ IN CASE WHEN prev IS NOT NULL THEN [1] ELSE [] END |
    CREATE (prev)-[:NEXT]->(t)
)
RETURN t.n AS turn_n
```

---

## Q6: `write_decision`
- **File:** [`q6_write_decision.cypher`](file:///d:/projects/Nell%20Ai/primer/backend/app/graph/queries/q6_write_decision.cypher)
- **Target Graph:** `session_<id>` (Working Memory)
- **Parameters:** `$decision_id`, `$ts`, `$kind`, `$summary`, `$memory_used`, `$session_id`
- **Purpose:** Creates a reasoning provenance `Decision` node (`select_skill`, `diagnose`, `hint`, `regress`, `advance`, `return`) capturing the exact explanation trace.
- **Cypher:**
```cypher
MATCH (s:Session {id: $session_id})
CREATE (d:Decision {
    id:          $decision_id,
    ts:          $ts,
    kind:        $kind,
    summary:     $summary,
    memory_used: $memory_used,
    session_id:  $session_id
})
CREATE (s)-[:MADE_DECISION]->(d)
RETURN d.id AS decision_id
```

---

## Q7: `get_session_turns`
- **File:** [`q7_get_session_turns.cypher`](file:///d:/projects/Nell%20Ai/primer/backend/app/graph/queries/q7_get_session_turns.cypher)
- **Target Graph:** `session_<id>` (Working Memory)
- **Parameters:** `$session_id` (string)
- **Purpose:** Fetches all session turns in sequence plus session metadata for memory consolidation into `child_<id>`.
- **Cypher:**
```cypher
MATCH (s:Session {id: $session_id})
OPTIONAL MATCH (s)-[:HAS_TURN]->(t:Turn)
WITH s, t
ORDER BY t.n ASC
RETURN
    s.id           AS session_id,
    s.child_id     AS child_id,
    s.started_at   AS started_at,
    s.graph_mode   AS graph_mode,
    s.target_skill AS target_skill,
    collect({
        n:                t.n,
        problem_id:       t.problem_id,
        skill_id:         t.skill_id,
        op:               t.op,
        a:                t.a,
        b:                t.b,
        answer:           t.answer,
        given:            t.given,
        correct:          t.correct,
        misconception_id: t.misconception_id,
        hint_level:       t.hint_level,
        hint_style:       t.hint_style,
        ts:               t.ts
    }) AS turns
```

---

## Q8: `decision_path`
- **File:** [`q8_decision_path.cypher`](file:///d:/projects/Nell%20Ai/primer/backend/app/graph/queries/q8_decision_path.cypher)
- **Target Graph:** `child_<id>` or `session_<id>`
- **Parameters:** `$decision_id` (string)
- **Purpose:** Traces the justification subgraph for a specific decision by finding the `Decision` node, its `CHOSE` target, and all `BECAUSE` nodes and edges for visual provenance in the Why panel.
- **Cypher:**
```cypher
MATCH (d:Decision {id: $decision_id})
OPTIONAL MATCH (d)-[:CHOSE]->(chosen)
OPTIONAL MATCH (d)-[b:BECAUSE]->(reason)
RETURN
    d.id                      AS decision_id,
    d.kind                    AS kind,
    d.summary                 AS summary,
    d.memory_used             AS memory_used,
    d.ts                      AS ts,
    labels(chosen)[0]         AS chosen_label,
    chosen.id                 AS chosen_id,
    collect({
        role:        b.role,
        label:       labels(reason)[0],
        id:          reason.id,
        name:        CASE WHEN reason.name IS NOT NULL THEN reason.name ELSE reason.id END,
        confidence:  reason.confidence
    })                        AS reasons
```
