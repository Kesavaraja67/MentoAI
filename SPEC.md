# NELL: SPEC (v2, the Primer vision)

Entry for Graph Hacks: Context for AI Agents (WeMakeDevs x FalkorDB), Oct 15 to 18, 2026.
Replaces the arithmetic-only "Primer" spec. Backend first. Frontend references arrive later.

Place this file at `docs/SPEC.md`. The build agent treats it as the source of truth.

---

## 0. One paragraph

Nell is a voice-first companion that learns with one person over time. Anyone can talk to it about anything: why the sky is blue, a dragon story, whether lying is ever okay, how to start a fraction, what to do on a bad day. There are no age bands and no fixed curriculum. What makes it a Primer rather than a chatbot is memory: everything Nell learns about the person (what they understand, what confuses them, what they love, whose names they mention, which stories they are inside, which ways of teaching actually worked) lives in a FalkorDB graph, and every teaching decision Nell makes is written back as a traceable path through that graph. The model decides. The graph remembers, connects, and explains.

Tagline for the README: **"A tutor that remembers who you are becoming."**

## 1. What changed from v1 and why

| v1 (arithmetic Primer) | v2 (Nell) |
|---|---|
| Ages 5 to 7, arithmetic only | No age limit, any topic, any language the models handle |
| Code checked answers and classified mistakes | Models judge understanding, from evidence stored in the graph |
| 13 seeded skills in a fixed DAG | Concept map grows on demand from what the person asks |
| Tap and type UI | Voice conversation is the product; text is the fallback |
| LLM was only a wording engine | LLM agents plan, teach, observe and reflect; the graph is their shared memory |

Reuse from the existing zip: `docker-compose.yml` pattern, `graph/client.py`, `config.py` pattern, provider allowlist (SSRF protection), test layout, MCP server skeleton. Delete: `engines/problems.py`, `assessor.py`, `mastery.py`, the 13-skill seed, answer-leak validators, template hints (except as a test double).

## 2. The honest boundary on "nothing deterministic"

Everything pedagogical and conversational is model-decided: what to say, how to explain, what to teach next, what counts as understanding, when to tell a story, how to respond to emotion, what to remember, what to revisit.

Three things stay deterministic on purpose, and the README says so plainly:

1. **Persistence and traversal.** Cypher is a database. It returns the same rows for the same graph. That is what makes the memory trustworthy.
2. **Schema validation of model output.** Every agent returns JSON that is validated before it touches the graph. A bad write is retried or dropped, never half-applied.
3. **Child-safety rails.** The input triage result gates the response mode, and unsafe output is blocked. Removing this because it is "deterministic" would be a mistake for a product that talks to children. Judges will probe it.

Do not add arithmetic checkers, keyword rules for misconceptions, fixed curricula, mastery thresholds, or template replies. If you feel the urge to hardcode a judgement, make it a model call that cites graph evidence.

## 3. Judging reality (read before building)

Rules that decide this, from the hackathon page:

- Rule 2 and 3: FalkorDB must be primary and the product must stop working in its useful form without the graph. Build a **Graph Off** switch (section 12) that proves it.
- Rule 6: only public, synthetic, or your own data. Demo personas are synthetic. Show a banner telling visitors not to share real personal details, auto-expire visitor graphs, and give a one-click "forget me".
- Rule 10: repo, README with setup + graph model, the Cypher the product depends on, demo video, live deployment or full local setup, named tracks.
- Rule 11: disclose AI assistants. Write `docs/AI_DISCLOSURE.md`.
- Rules 12 and 13: **you must be able to explain the graph model, queries, architecture and decisions, and projects entirely AI-generated without participant understanding may be rejected.** The build agent writes `docs/EXPLAIN.md`; you read it, run the queries yourself in the FalkorDB browser, and can answer every question in it without notes.

Tracks to name on submission: **Track 2 Agent Memory and Coordination (primary)** and **Track 1 Agents That Act on Connected Data (secondary)**. Do not claim Track 3 (Company Brain) unless the grown-up/teacher shared brain is truly built; naming a track you cannot defend costs more than it gains. Note: only the Rules page was available when this spec was written. Re-read the Tracks page and align the README wording to its exact criteria.

What the Agent Harness winners had in common (checked in their repos): see `docs/WINNING_PATTERNS.md` section in the master prompt; the short version is a hard, nameable problem, a property enforced in structure rather than in a prompt, a visible evidence trail, tests on the judgement logic, and a README that states limitations plainly.

## 4. Product behaviour

### 4.1 Conversation
- Voice-first. The person speaks, Nell answers aloud, subtitles show both sides live.
- Interruptible (barge-in). If the person talks over Nell, Nell stops and the stored turn is truncated to what was actually spoken.
- "New chat" starts a new Conversation for the same Learner. Memory persists across conversations. A "fresh learner" option creates a new graph.
- Demo access only: choose a persona or start blank. No passwords.

### 4.2 What Nell does that a chatbot does not
1. **Callbacks.** "Yesterday you wondered why octopuses have three hearts. Today's question about blood connects to that." The callback must come from a graph traversal, and the trace must show the path.
2. **Bridging.** New ideas are introduced from something the person already knows or loves, found by multi-hop traversal from the new concept to known concepts and interests.
3. **Diagnosing confusion upstream.** When the person is stuck on X, Nell traces X's prerequisites in this person's own concept map to find the weakest supported one, and goes there first.
4. **Sagas.** Ongoing stories that feature the person's own names, pets, places and interests, and that teach concepts. Chapters continue across days.
5. **Teaching style learning.** Which moves (analogy, story, question, worked example, hands-on, humour, retrieval practice) worked for this person on which kinds of concepts. Learned from outcomes, not set by rules.
6. **Open loops.** At session end, Nell records unfinished curiosities, saga cliffhangers, and ideas worth revisiting. The next conversation can open with one, chosen by the Strategist.
7. **Character and wisdom.** Ethical dilemmas and big questions are first-class: Nell explores them Socratically, records the person's reasoning (not a verdict), and can revisit later.
8. **Grown-up view.** A digest for a parent or teacher generated from the graph: what they explored, what is shaky, what lit them up, what to try. Supplement, not replacement.
9. **Visuals.** Nell can call a `show` tool to put diagrams, concept maps, story cards and illustrations on screen (section 9).

### 4.3 Registers instead of ages
Nell estimates a **register** (vocabulary, sentence length, abstraction comfort, language, pace) from the person's own speech and updates it every few turns. It is stored as free text plus a confidence, never as an age. Nell never asks age. A sixty-year-old learning fractions and a six-year-old learning why the moon follows the car both get a fitting register.

## 5. Architecture

```
 Browser (mic, speaker, subtitles, graph panel)
     |  WebSocket (voice+events)         REST (conversations, learner, trace)
     v
 FastAPI app ----------------------------------------------+
   |  Conversation Orchestrator                            |
   |    hot path:  Triage || Context Assembly  ->  Companion (streams)  ->  Sentence chunker -> TTS
   |    cold path: Listener -> Cartographer -> Strategist (async, after each turn)
   |    session end: Reflector (consolidation, open loops, grown-up digest)
   |  Agent runtime: tool-calling loop, schema validation, provider fallback
   |  Graph tools (Cypher): the only way agents touch memory
   v
 FalkorDB (graph per learner, optional shared "commons" graph)
```

Agents never talk to each other directly. They coordinate by reading and writing graph state (Plan, Decision, Observation, OpenLoop nodes). The event bus only mirrors those writes to the UI.

### 5.1 Agents

| Agent | Speaks to person? | Model tier | Runs | Reads graph via | Writes |
|---|---|---|---|---|---|
| Triage | no | fast | hot path, parallel with context assembly | none | SafetyEvent, turn mode |
| Companion (Nell) | yes | voice (streaming, low latency) | hot path | context pack + tools below | Turn, spoken_text |
| Listener | no | fast | after each turn, async | recent turns, candidate concepts | Evidence, Misconception, Curiosity, Interest, Entity, Emotion, register |
| Cartographer | no | smart | when Listener reports a new or thin concept | vector match + neighbourhood | Concept, PREREQUISITE_OF, ANALOGOUS_TO, PART_OF, TOUCHES |
| Strategist | no | smart | after each turn, async, writes the plan for the next turn | bridge, gap, style and open-loop queries | Plan, Decision, BECAUSE edges |
| Storyteller | via Companion | smart | invoked by Companion tool or Strategist plan | saga state, entities, target concept | Tale, Chapter, FEATURES, TEACHES |
| Guardian | no | fast | audits every turn async; blocks in hot path only when Triage flagged | turn text | SafetyEvent, ParentFlag |
| Reflector | no | smart | conversation end or idle timeout | whole conversation + neighbourhoods | merges, summaries, OpenLoop, Digest |

Latency rule: the hot path may do at most one parallel batch of graph reads before the first model token, and the Companion may make at most 2 tool calls per turn. Everything else is async. Target first audio under about 2 seconds on a good connection. Measure and report the real number in the README; do not claim a number you did not measure.

### 5.2 Hot path (per spoken turn)
1. Transcript arrives (final). Write `Turn(role=person)`.
2. In parallel: **Triage** (fast model, structured output: mode = normal | care | refuse_redirect, categories) and **Context Assembly** (section 6.3, 4 to 6 Cypher queries run concurrently).
3. **Companion** gets: system persona + safety constitution + register + the Plan the Strategist left for this moment + the context pack + the last turns. It may call `recall`, `bridge`, `tell_story`, `show`, `note_wonder`.
4. Output streams token by token. A sentence chunker emits subtitle deltas and TTS jobs per sentence.
5. On completion write `Turn(role=nell, spoken_text)`; enqueue the cold path.

### 5.3 Cold path (async, after each turn, never blocks speech)
Listener, then Cartographer if needed, then Strategist. Each writes graph state and emits `viz.event`s so the UI shows memory forming. If a cold-path step fails, log a `PipelineFault` node and continue; the next turn still works.

### 5.4 Session end
Reflector runs on explicit end, on "new chat", and after 10 minutes idle. It must be idempotent.

## 6. Graph model (FalkorDB)

One graph per learner: `learner_<id>`. Optional stretch: shared graph `commons` holding concept expansions the Cartographer produced for anyone, so repeat topics are copied instead of regenerated (cheaper, faster). Cross-graph links are by `Concept.key` only; never design a query that needs both graphs at once.

### 6.1 Nodes

| Label | Key properties | Meaning |
|---|---|---|
| Learner | id, display_name, created_at, language, register_text, register_conf, voice_pref, expires_at | The person |
| Conversation | id, title, started_at, ended_at, summary, mood_arc | One chat |
| Turn | id, idx, role, text, spoken_text, ts, emotion, intent, mode | One utterance |
| Concept | key, name, summary, domain, embedding, created_by, created_at | Anything learnable, created on demand |
| Evidence | id, kind, quote, verdict, strength, ts | What the person did that shows understanding or confusion. kind: explained, applied, asked, misused, teachback, guessed |
| Misconception | id, statement, status, first_seen, last_seen | A specific wrong model the person holds |
| Curiosity | id, text, intensity, status | Open question or wonder. status: open, explored, parked |
| Interest | name, summary | Things they love |
| Entity | id, name, kind, facts | People, pets, places, objects in their life (synthetic in demo) |
| Tale | id, title, premise, status, last_summary | A saga |
| Chapter | id, idx, text, cliffhanger, ts | A saga chapter |
| TeachingMove | name | analogy, story, socratic, worked_example, hands_on, retrieval, humour, visual, silence, reframe |
| Plan | id, for_conversation, text, ts, consumed | Strategist note left for the next Companion turn |
| Decision | id, agent, kind, rationale, ts, confidence | Any consequential choice by an agent |
| Dilemma | id, question, stance_text, ts | Ethical or meaning question the person reasoned about |
| OpenLoop | id, text, kind, priority_note, status | Thing to come back to |
| Digest | id, text, ts, audience | Grown-up summary |
| SafetyEvent | id, category, severity, action, ts | Triage or Guardian finding |
| PipelineFault | id, stage, error, ts | Cold-path failure record |

### 6.2 Relationships

```
(Learner)-[:HAD]->(Conversation)-[:HAS_TURN]->(Turn)-[:NEXT]->(Turn)
(Turn)-[:PRODUCED]->(Evidence)-[:ABOUT]->(Concept)
(Learner)-[:HOLDS]->(Misconception)-[:ABOUT]->(Concept)
(Learner)-[:WONDERS]->(Curiosity)-[:SPARKED_BY]->(Turn); (Curiosity)-[:RELATES_TO]->(Concept)
(Learner)-[:LOVES {strength}]->(Interest)-[:TOUCHES]->(Concept)
(Learner)-[:MENTIONED {times, last_ts}]->(Entity)
(Concept)-[:PREREQUISITE_OF {why, conf}]->(Concept)
(Concept)-[:ANALOGOUS_TO {via, conf}]->(Concept)
(Concept)-[:PART_OF]->(Concept)
(Learner)-[:KNOWS {depth, confidence, trend, last_evidence_ts}]->(Concept)   // written by Listener/Reflector from Evidence, with rationale
(Learner)-[:ON_JOURNEY]->(Tale)-[:HAS_CHAPTER]->(Chapter); (Tale)-[:TEACHES]->(Concept); (Tale)-[:FEATURES]->(Entity|Interest)
(Decision)-[:CHOSE]->(Concept|TeachingMove|Tale|OpenLoop)
(Decision)-[:BECAUSE {note}]->(Evidence|Turn|Curiosity|Misconception|Entity|Interest|SafetyEvent)
(Decision)-[:MADE_IN]->(Turn)
(Decision)-[:USED]->(TeachingMove)-[:LED_TO {outcome, note}]->(Evidence)
(Plan)-[:WRITTEN_BY]->(Decision)
(Learner)-[:EXPLORED]->(Dilemma)
(OpenLoop)-[:ABOUT]->(Concept|Tale|Curiosity)
(Digest)-[:SUMMARISES]->(Conversation)
```

`KNOWS.depth` and `confidence` are numbers produced by a model with a stored rationale, not by a formula. Cypher may aggregate (counts, recency, trend inputs) but the judgement is the Listener's or Reflector's.

### 6.3 Queries the product depends on (each lives in `backend/app/graph/queries/*.cypher`)

Every query ships with: intent, caller agent, parameters, an example result, and a test on a fixture graph. Verify each against the live container before relying on it. Syntax for vector search and graph algorithms differs by FalkorDB version, so read the docs for the pinned image and record the version in the README.

| Id | Name | What it does | Used by |
|---|---|---|---|
| G1 | learner_snapshot | Register, top interests, active curiosities, current sagas, open loops, recent entities | Context Assembly |
| G2 | semantic_recall | Vector search over Concept, Curiosity, Chapter and Turn embeddings for the current utterance, then expand 1 hop | Context Assembly, `recall` tool |
| G3 | bridge_paths | Shortest and near-shortest paths from a target concept to concepts the learner KNOWS or LOVES via interests, scored by path confidence and evidence recency | Strategist, `bridge` tool |
| G4 | weak_prerequisites | Upstream traversal `(p)-[:PREREQUISITE_OF*1..5]->(target)` returning prerequisites with thin or declining evidence or an open Misconception | Strategist |
| G5 | style_outcomes | Aggregate TeachingMove outcomes for this learner, optionally restricted to concepts near the target by graph distance | Strategist |
| G6 | open_loops_ranked | Open loops with their related concept, age, and connection to today's topics | Strategist, session open |
| G7 | saga_state | Active Tale, last chapter, cliffhanger, featured entities, taught concepts | Storyteller |
| G8 | write_evidence | Create Evidence, link Turn and Concept, upsert KNOWS | Listener |
| G9 | write_concept_neighbourhood | Upsert Concepts and typed edges produced by the Cartographer, idempotent on `key` | Cartographer |
| G10 | write_decision | Create Decision with CHOSE, BECAUSE and MADE_IN edges | Strategist, Companion tools |
| G11 | decision_trace | Neighbourhood around a Decision for the Why panel | API, UI |
| G12 | mind_view | Subgraph for the live constellation: top K concepts by recent activity plus their edges | API, UI |
| G13 | merge_duplicates | Candidate duplicate Concepts (vector near + name near) for the Reflector to confirm and merge | Reflector |
| G14 | hubs_and_clusters | Centrality and connected components over the learner's concept graph (use FalkorDB graph algorithms if available in the pinned version) to name the person's "worlds" | Reflector, Digest |
| G15 | forget_learner | Delete graph | API |

Rule 3 argument, in one sentence for the README: G3, G4, G5 and G14 are multi-hop and algorithmic over a graph that the models themselves wrote, and the Companion's callbacks, bridges and style choices come out of them; remove the graph and Nell has no past.

### 6.4 Embeddings
Local, free, no GPU: a small multilingual embedding model through an ONNX runtime library such as `fastembed` (verify current availability and model names), 384 to 768 dimensions, created at write time for Concept, Curiosity, Chapter and Turn summaries. Provider embeddings are an optional fallback. Store the model name in the graph so a re-embed is possible.

## 7. Agent runtime

- Provider-agnostic OpenAI-compatible client, tool calling, JSON-schema outputs validated with pydantic, retry-with-repair once, then drop and log `PipelineFault`.
- Tiers via env: `LLM_FAST_*`, `LLM_SMART_*`, `LLM_VOICE_*`, each with an ordered fallback list. Circuit breaker per provider. Never hardcode model names; a `scripts/check_providers.py` lists what each configured key can actually do (streaming, tool calls, JSON mode, observed latency) and the build picks from the result. Free-tier limits and model names change often; test two providers before choosing.
- If a free model has unreliable native tool calling, use a JSON-action protocol (`{"tool": "...", "args": {...}}`) with the same validation. The tool set is identical either way.
- Provider allowlist (existing `providers.py`) stays. Add only providers you tested. BYOK header allowed for demos; never log keys.
- AWS Bedrock is optional. Do not depend on it until you confirm your student credits cover it and the models are enabled in your region.
- Prompts live in `backend/app/agents/prompts/*.md`, versioned, with a one-line changelog each. They contain the safety constitution (section 10) and the register guidance.
- A deterministic **fake model** exists for unit tests only. It is never reachable at runtime.

### 7.1 Companion tools (all Cypher-backed)
`recall(query)`, `bridge(concept)`, `weak_prereqs(concept)`, `tell_story(concept?, entity?)`, `show(kind, payload)`, `note_wonder(text)`, `park_for_later(text)`. Each call writes a Decision node with BECAUSE edges so the UI can show why.

## 8. Voice

Free by design. Two modes behind one interface; the app always works in Mode A.

**Mode A (default, ships first):** browser speech recognition and browser speech synthesis. Zero server cost. Chrome is the supported demo browser, because recognition support and the audio route differ by browser; say so in the README and show a clear message in unsupported browsers with text fallback. The server only sees text.

**Mode B (stretch, only after the full loop works):** server-side speech to text with a small open Whisper-family model, server-side text to speech with a small open model (for example Kokoro or Piper; verify license and quality yourself), streamed as audio chunks. Needs CPU headroom on the EC2 box; benchmark before committing. Do not use unofficial scraped TTS endpoints for the submission.

Both modes share the protocol in section 9. Barge-in, sentence-level streaming, and subtitle events are identical.

## 9. Realtime protocol (freeze this early so the frontend can build against it)

Document it in `docs/PROTOCOL.md` and export `openapi.json` at build. WebSocket `/ws/conversations/{id}` with JSON messages.

Client to server: `hello {learner_id, mode}`, `transcript.partial {text}`, `transcript.final {text}`, `audio.chunk {pcm16_b64}` (mode B), `barge_in {spoken_chars}`, `control {mute|end|pause}`.

Server to client:
- `state {listening | thinking | speaking}`
- `subtitle.person {text, final}`, `subtitle.nell {delta, sentence_id}`
- `tts.chunk {sentence_id, audio_b64, fmt}` (mode B) or `tts.text {sentence_id, text}` (mode A speaks it locally)
- `viz.event {op: add_node|add_edge|pulse|trace, payload}` mirroring graph writes in near real time
- `visual {id, kind, payload}` from the `show` tool. Kinds: `svg`, `mermaid`, `concept_map`, `story_card`, `number_line`, `timeline`. SVG from a model is untrusted: the server strips scripts, event handlers and external references before sending.
- `decision {id, summary}` pointer the UI can use to open the Why panel
- `error {code, recoverable}`

REST: `POST /api/learners`, `GET /api/personas`, `POST /api/learners/{id}/conversations`, `GET /api/learners/{id}/conversations`, `GET /api/conversations/{id}/turns`, `GET /api/learners/{id}/mind`, `GET /api/decisions/{id}/trace`, `GET /api/learners/{id}/digest`, `POST /api/learners/{id}/forget`, `POST /api/admin/graph-mode {on|off}` (demo only), `GET /api/health`, `GET /api/providers/status`.

## 10. Safety constitution (Guardian and Companion prompts, plus Triage gate)

Written for a product any age may use, where some users are young:

- Warm, honest, never condescending; never pretends to be human; says when unsure; never invents sources.
- Never asks for or stores contact details, school, address, or other identifying information; if volunteered, gently steers away and does not write it as a durable fact.
- Care mode when Triage flags distress, self-harm, abuse, or danger: slow down, validate, encourage talking to a trusted adult, provide appropriate help-line guidance for the region if known, and write a `ParentFlag` without graphic detail. Never ends the conversation abruptly.
- Declines clearly unsafe requests with a kind redirect that offers a safe adjacent topic.
- Does not give medical, legal or financial directives; explains and points to a trusted adult or professional.
- Does not manipulate, flatter to retain, or build dependency; encourages friends, family, teachers, and offline curiosity; may suggest a break.
- Big questions (ethics, religion, politics): explores reasoning and multiple views fairly, does not push its own stance on contested topics.
- Mic audio is never stored. Transcripts live only in the learner graph, which can be forgotten in one click and expires for visitor graphs.

Add `evals/safety/` with at least 30 red-team prompts across these lines and report pass rates honestly.

## 11. Personas and the memory proof (demo data)

Three synthetic personas, created by **replaying scripted conversations through the real pipeline** (not by hand-writing graph rows), then exporting the graph to `fixtures/personas/*.jsonl` so restore is fast and the history is genuine:

1. **Mira**, a young curious learner: octopuses, drawing, a pet named Biscuit, shaky on "why things float".
2. **Arjun**, a teenager: fairness, cricket statistics, a misconception about probability.
3. **Lakshmi**, an adult returning learner: wants to understand fractions she was never taught, hates being rushed.

Each has two prior days of history so the live demo can show day 3.

## 12. Graph Off (proof for Rule 3)

`GRAPH_MODE=off` swaps every graph tool for a no-op that returns empty results and stops writes. The Companion still talks, but it has no past, no bridges, no saga, no trace. The UI has a visible toggle in the demo drawer. The demo video shows the same three questions asked both ways.

## 13. Evals instead of pretend determinism

Because the behaviour is model-driven, quality is proven by repeated scenario runs, not by assert-equals.

- `evals/scenarios/*.yaml`: scripted multi-session scenarios with graph-derived assertions judged by an LLM judge plus structural checks (for example "the Day 2 reply references octopus hearts, and the trace shows a path from the new concept to the old Evidence node").
- Each scenario runs N times (default 5). Report pass rate, median latency, and cost proxy. Include the table in the README, including failures.
- `make eval-graph-off` runs the same scenarios with the graph disabled to show the delta.
- Graph query tests run against a real FalkorDB container, not mocks.

## 14. Testing

- Unit: schema validation, sentence chunker, barge-in truncation, SVG sanitiser, provider fallback and circuit breaker, safety gate wiring.
- Integration: every Cypher query on fixture graphs, idempotent upserts, forget, expiry.
- WebSocket protocol tests with a fake model.
- E2E (Playwright, skill `webapp-testing`) once the frontend exists: speak via injected transcript events, assert subtitles, Why panel and graph panel update.
- CI: lint, type check, unit and integration. State what CI does not cover.

## 15. Deployment

- `docker compose up` runs FalkorDB (bound to localhost or the private network only), backend, frontend, Caddy for HTTPS (browsers require HTTPS for the microphone outside localhost).
- One EC2 instance with student credits. Set a billing alarm before anything else. Confirm what your credits cover; do not assume.
- `.env.example` complete. Secrets never in the repo or the client bundle.
- Live deployment URL plus a no-key mode: the deployed demo must work for judges without them bringing a key (server-side keys with rate limits and a kill switch) and must say clearly when it is rate limited.
- Rate limiting per IP and per learner; a daily spend cap in code.

## 16. Documentation set (winners shipped deep docs)

`README.md` (pitch, track claim, architecture diagram, setup, graph model, link to every query), `docs/GRAPH_MODEL.md`, `docs/QUERIES.md`, `docs/PROTOCOL.md`, `docs/DECISIONS.md` (including rejected shortcuts), `docs/KNOWN_LIMITATIONS.md` (plain and specific), `docs/VERIFICATION.md`, `docs/AI_DISCLOSURE.md`, `docs/EXPLAIN.md` (30 likely judge questions with answers grounded in the code), `docs/DEMO_SCRIPT.md`.

## 17. Cut lines (about 55 hours remain from Oct 16 evening)

Must ship: graph core and queries, Companion with callbacks and bridging, Listener, Strategist with decision traces, Mode A voice with subtitles and barge-in, graph panel events, Graph Off, three personas, README with real eval numbers, deployment, video.

Cut in this order if behind: Mode B voice, MCP server, commons graph, Dilemma tracking polish, graph algorithms in G14, Storyteller multi-chapter (keep one chapter plus cliffhanger).

## 18. Definition of done

A judge can open the URL, pick Mira, say "why does Biscuit float in the pool but my toy boat sinks when it fills up", hear Nell answer, see subtitles, see new nodes appear, click the reply and see the path that made Nell connect it to yesterday's octopus talk, flip Graph Off and watch the same question lose all of that, and open the grown-up digest. And you can explain every box in section 5 aloud.