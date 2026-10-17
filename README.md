# MentoAI: A Tutor That Remembers Who You Are Becoming

[![FalkorDB](https://img.shields.io/badge/FalkorDB-Graph%20Memory-red)](https://falkordb.com/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2015-black)](https://nextjs.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

> **Entry for Graph Hacks: Context for AI Agents (WeMakeDevs × FalkorDB), Oct 15–18, 2026.**  
> **Primary Track:** Track 02 — Agent Memory & Coordination  
> **Secondary Track:** Track 01 — Connected Data & Reasoning Traces  

---

## 0. The Vision

Inspired by the Young Lady's Illustrated Primer in Neal Stephenson's *The Diamond Age*, **MentoAI** is a voice-first lifelong companion that learns with one person over time.

Anyone can talk to it about anything: why the sky is blue, why octopuses have three hearts, how to scale a fraction in sourdough baking, or what to do on a bad day. There are **no age bands** and **no fixed curricula**.

What makes it MentoAI rather than a chatbot is **memory**: everything MentoAI learns about the person (what they understand, what confuses them, what they love, whose names they mention, and which ways of teaching actually worked) lives in a **FalkorDB graph**. Every teaching decision MentoAI makes is written back as a traceable path through that graph.

> **"The model decides. The graph remembers, connects, and explains."**

---

## 1. Hackathon Track Alignment

| Track | Alignment & Implementation |
|---|---|
| **Track 02: Agent Memory & Coordination (Primary)** | All 7 agents (Triage, Companion, Listener, Cartographer, Strategist, Reflector, Guardian) coordinate **strictly through the FalkorDB graph**. Agents never call each other directly; they read and write graph state (`Plan`, `Decision`, `Evidence`, `Curiosity`, `OpenLoop`). |
| **Track 01: Connected Data & Reasoning Traces (Secondary)** | Every pedagogical decision is justified by multi-hop graph paths (`[:PREREQUISITE_OF]`, `[:ANALOGOUS_TO]`, `[:BECAUSE]`). The **Why Panel** displays full multi-hop provenance for why MentoAI made every move. |

---

## 2. Architecture

```
 Browser (Microphone, Subtitles, Orb, Constellation Mind, Why Panel)
     │   ▲ WebSocket: /ws/conversations/{id}
     ▼   │ REST: /api/learners, /api/mind, /api/decisions
 FastAPI Backend
   ├── Hot Path (Low Latency):
   │     Triage (Safety Gate) || Context Assembly (G1 Snapshot, G2 Vector Recall)
   │     ➔ Companion (Streaming) ➔ Sentence Chunker ➔ Web Speech Audio & Subtitles
   ├── Cold Path (Async Background):
   │     Listener (G8) ➔ Cartographer (G9) ➔ Strategist (G3, G4, G5, G10) ➔ Guardian (Audit)
   │     Emits real-time `viz.event`s to active WebSocket clients
   ├── Session End:
   │     Reflector (G6, G13, G14) ➔ Grown-Up Digest & Open Loops
   └── FalkorDB Multi-Tenant Storage:
         Isolated graph per learner (`learner_<id>`) with 15 Cypher queries (G1–G15)
```

---

## 3. The Multi-Agent Suite

| Agent | Speaks Aloud? | Tier | When it Runs | Reads Graph Via | Writes to Graph |
|---|---|---|---|---|---|
| **Triage** | No | Fast | Hot path (parallel with context assembly) | None (stateless) | `SafetyEvent`, turn mode |
| **Companion** | **Yes** | Voice | Hot path | G1 Snapshot + G2 Semantic Recall | `Turn`, spoken text |
| **Listener** | No | Fast | Cold path (async post-turn) | Recent turns | `Evidence`, `Curiosity`, `Interest`, `Entity`, register |
| **Cartographer** | No | Smart | Cold path (when new concepts appear) | Candidate concept keys | `Concept`, `PREREQUISITE_OF`, `ANALOGOUS_TO`, `PART_OF` |
| **Strategist** | No | Smart | Cold path (async post-turn) | G3 Bridge, G4 Weak Prereq, G5 Style | `Plan`, `Decision`, `[:BECAUSE]` provenance edges |
| **Reflector** | No | Smart | Session end / idle timeout | Whole conversation | `OpenLoop`, `Digest`, deduplication merges (G13) |
| **Guardian** | No | Fast | Cold path (async audit) | Spoken turn text | Safety events, PII flags |

---

## 4. FalkorDB Cypher Queries (G1–G15)

All queries are defined as standalone `.cypher` files under [`backend/app/graph/queries/`](backend/app/graph/queries/):

| Query | Name | Operation | Used By |
|---|---|---|---|
| **G1** | `learner_snapshot` | Returns register, top interests, active curiosities, open loops, and recent entities | Context Assembly |
| **G2** | `semantic_recall` | 384-d vector cosine search + 1-hop expansion over concept embeddings | Context Assembly / `recall` tool |
| **G3** | `bridge_paths` | Shortest paths linking target concepts to things the learner KNOWS or LOVES | Strategist / `bridge` tool |
| **G4** | `weak_prerequisites` | 1–5 hop upstream traversal finding concepts with thin evidence or misconceptions | Strategist |
| **G5** | `style_outcomes` | Historical success rates of pedagogical moves for this learner | Strategist |
| **G6** | `open_loops_ranked` | Ranked unresolved curiosities and saga cliffhangers for session opening | Strategist / Session Open |
| **G7** | `saga_state` | Retrieves active Tale, current chapter cliffhanger, and featured entities | Storyteller |
| **G8** | `write_evidence` | Creates Evidence node, links to Turn and Concept, upserts KNOWS relation | Listener |
| **G9** | `write_concept_neighbourhood` | Idempotent upsert of Concept nodes and semantic relationships | Cartographer |
| **G10** | `write_decision` | Creates Decision with CHOSE and explicit BECAUSE provenance edges | Strategist / Companion |
| **G11** | `decision_trace` | Multi-hop provenance neighborhood for the Why Panel | UI / Why Panel |
| **G12** | `mind_view` | Subgraph of top active concepts and typed links for Constellation visualizer | UI / Mind Graph |
| **G13** | `merge_duplicates` | Finds candidate duplicate concepts via cosine similarity and name overlap | Reflector |
| **G14** | `hubs_and_clusters` | Computes graph centrality and connected components | Reflector / Digest |
| **G15** | `forget_learner` | Drops the tenant graph for complete privacy erasure | API (Rule 6) |

---

## 5. Hackathon Rule 3 Proof: The Graph Off Switch

> **Rule 3 Argument:** *G3, G4, G5, and G14 are multi-hop algorithmic queries over a graph that the models themselves wrote, and the Companion's callbacks, bridges, and style choices come directly out of them; remove the graph and MentoAI has no past.*

We proved this directly in the software:
- A prominent **Graph: ON / OFF** toggle lives in the top bar and at `POST /api/admin/graph-mode`.
- When set to `OFF`, all graph queries return empty results, writes are bypassed, and MentoAI degrades to a generic stateless chatbot with zero personal memory, no bridges to Biscuit the dog or octopuses, and an empty Why Panel.

---

## 6. Pre-Built Synthetic Personas (3-Day Memory Proof)

1. **Mira (Curious 7yo)**: Loves octopuses (3 hearts), drawing, and swimming with her dog Biscuit. Shaky on buoyancy and water displacement.
2. **Arjun (High Schooler)**: Passionate about cricket statistics and sports analytics. Holds gambler's fallacy misconception on probability.
3. **Lakshmi (Adult Learner)**: Sourdough baker returning to mathematics. Desires intuitive understanding of fractions and proportions without being rushed.

---

## 7. Quickstart

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local frontend dev)
- Python 3.10+ (for local backend dev)

### Launch via Docker
```bash
docker compose up -d
```
- Frontend: `http://localhost:3000`
- Backend API Docs: `http://localhost:8000/docs`
- FalkorDB: `localhost:6379`

### Run Backend Tests
```bash
cd backend
pytest tests/ -v
```

---

## 8. Documentation Set

- [Graph Ontology & Model](docs/GRAPH_MODEL.md)
- [Cypher Queries Reference](docs/QUERIES.md)
- [Realtime WebSocket Protocol](docs/PROTOCOL.md)
- [Technical Explanation & Judge Q&A (30 Questions)](docs/EXPLAIN.md)
- [3-Minute Demo Video Script](docs/DEMO_SCRIPT.md)
- [AI Disclosure (Rule 11)](docs/AI_DISCLOSURE.md)
