# MentoAI: FalkorDB Graph Model & Ontology (v2)

Entry for **Graph Hacks: Context for AI Agents** (WeMakeDevs × FalkorDB).  
Track 02 (Agent Memory & Coordination) & Track 01 (Connected Data & Reasoning Traces).

---

## 1. Graph Architecture & Multi-Tenancy

Every learner has their own isolated FalkorDB graph:
- **Tenant Key:** `learner_<learner_id>` (e.g. `learner_mira`, `learner_arjun`)
- **Isolation:** Strict graph-level isolation guarantees zero cross-contamination of personal memory, fast queries, and single-command complete erasure (`GRAPH.DELETE`) for the "Right to be Forgotten" (Rule 6).

---

## 2. Node Ontology (19 Node Schemas)

| Label | Primary Properties | Description |
|---|---|---|
| `Learner` | `id`, `display_name`, `language`, `register_text`, `register_conf`, `voice_pref`, `created_at` | The human learning partner. Adapts dynamically to register instead of age bands. |
| `Conversation` | `id`, `title`, `started_at`, `ended_at`, `summary`, `mood_arc`, `status` | A single conversational session. |
| `Turn` | `id`, `role`, `text`, `spoken_text`, `ts`, `emotion`, `intent`, `mode` | Individual spoken or typed utterance. |
| `Concept` | `key`, `name`, `summary`, `domain`, `embedding`, `created_by`, `created_at` | Anything learnable, defined dynamically on-demand with 384-d fastembed vectors. |
| `Evidence` | `id`, `kind`, `quote`, `verdict`, `strength`, `depth`, `confidence`, `rationale`, `ts` | Grounded quotes demonstrating understanding or confusion. |
| `Misconception` | `id`, `statement`, `status`, `first_seen`, `last_seen` | A specific incorrect mental model held by the learner. |
| `Curiosity` | `id`, `text`, `intensity`, `status` | Questions or wonders sparked during dialogue. |
| `Interest` | `name`, `summary` | Passion or hobby (e.g. Octopuses, Cricket, Baking). |
| `Entity` | `id`, `name`, `kind`, `facts` | People, pets, places, or objects (e.g. "Biscuit" the dog). |
| `Tale` | `id`, `title`, `premise`, `status`, `last_summary` | Ongoing saga continuing across days. |
| `Chapter` | `id`, `idx`, `text`, `cliffhanger`, `ts` | Chapter in an episodic tale. |
| `TeachingMove` | `name` | Canonical moves (`analogy`, `story`, `socratic`, `worked_example`, `hands_on`, `retrieval`, `humour`, `visual`, `reframe`). |
| `Plan` | `id`, `text`, `ts`, `consumed` | Pedagogical guidance note created by Strategist for the Companion. |
| `Decision` | `id`, `agent`, `kind`, `chosen_move`, `rationale`, `confidence`, `ts` | Consequential choices made by agents. Anchor for the Why Panel. |
| `Dilemma` | `id`, `question`, `stance_text`, `ts` | Ethical or philosophical dilemmas explored Socratically. |
| `OpenLoop` | `id`, `text`, `kind`, `priority`, `status`, `ts` | Things to come back to in future sessions. |
| `Digest` | `id`, `text`, `topics`, `strengths`, `shaky_areas`, `offline_activities`, `ts` | Grown-up digest for parents and mentors. |
| `SafetyEvent` | `id`, `category`, `severity`, `action`, `notes`, `ts` | Flagged safety interventions or PII redactions. |
| `PipelineFault` | `id`, `stage`, `error`, `ts` | Cold-path async execution errors. |

---

## 3. Semantic Relationship Types

```cypher
// Conversation history
(Learner)-[:HAD]->(Conversation)-[:HAS_TURN]->(Turn)-[:NEXT]->(Turn)

// Comprehension & Evidence
(Turn)-[:PRODUCED]->(Evidence)-[:ABOUT]->(Concept)
(Learner)-[:HOLDS]->(Misconception)-[:ABOUT]->(Concept)
(Learner)-[:KNOWS {depth, confidence, rationale}]->(Concept)

// Curiosity & Passions
(Learner)-[:WONDERS]->(Curiosity)-[:SPARKED_BY]->(Turn)
(Curiosity)-[:RELATES_TO]->(Concept)
(Learner)-[:LOVES {strength}]->(Interest)-[:TOUCHES]->(Concept)
(Learner)-[:MENTIONED {times, last_ts}]->(Entity)

// Pedagogical Knowledge Graph
(Concept)-[:PREREQUISITE_OF {why, conf}]->(Concept)
(Concept)-[:ANALOGOUS_TO {via, conf}]->(Concept)
(Concept)-[:PART_OF]->(Concept)

// Episodic Sagas
(Learner)-[:ON_JOURNEY]->(Tale)-[:HAS_CHAPTER]->(Chapter)
(Tale)-[:TEACHES]->(Concept)
(Tale)-[:FEATURES]->(Entity)

// Provenance & Reasoning Trace (The Why Panel)
(Decision)-[:MADE_IN]->(Turn)
(Decision)-[:CHOSE]->(TeachingMove)
(Decision)-[:BECAUSE {note}]->(Evidence|Turn|Curiosity|Misconception|Interest|Entity)
(Plan)-[:WRITTEN_BY]->(Decision)
(Learner)-[:HAS_PLAN]->(Plan)

// Reflection & Loops
(OpenLoop)-[:ABOUT]->(Concept|Curiosity)
(Digest)-[:SUMMARISES]->(Conversation)
(Learner)-[:HAS_DIGEST]->(Digest)
```

---

## 4. Vector Indices

FalkorDB vector indices are provisioned on:
- `Concept.embedding` (384-dimensional cosine index)
- `Curiosity.embedding`
- `Turn.embedding`
- `Chapter.embedding`

These allow MentoAI to perform sub-10ms semantic recall (G2) connecting any incoming utterance to relevant past memories.
