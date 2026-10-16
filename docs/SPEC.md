# Primer: Product and Technical Spec

Submission for **Graph Hacks: Context for AI Agents** (WeMakeDevs x FalkorDB). Deadline: **Oct 18, 2026, 11:59 PM IST**.
Builder: solo developer. Implementation is done by an AI coding agent, reviewed by the human.

This file is the single source of truth. If code and this file disagree, stop and ask the human which one is right. Do not silently drift.

---

## 0. Ground rules for whoever reads this

1. **Scope is binding.** Section 3 lists what is out. Do not add it, even if it is easy.
2. **Every FalkorDB query in this spec is a draft.** Run each against a real FalkorDB container before relying on it. If a query fails or behaves differently, fix the query and record the fix in `docs/QUERIES.md`.
3. **The human must be able to explain every part** (hackathon Rules 12 and 13). Keep code small and readable. Prefer plain functions over clever abstractions.
4. **No fake success.** Never report a test as passing unless it ran. Never stub a feature and call it done.
5. **Synthetic data only** (Rule 6). No real children, no real names, no personal data anywhere.
6. **AI assistance is disclosed** (Rule 11). The README carries a disclosure section.

---

## 1. What Primer is

Primer is a web app that teaches arithmetic to children aged 5 to 7 (a synthetic child in the demo). It poses short story-wrapped problems. When the child gets one wrong, it does **not** say "wrong" and it does **not** give the answer. It:

1. Classifies the *kind* of mistake with deterministic rules.
2. Walks a prerequisite graph to find the real weak skill underneath.
3. Guides the child with a hint ladder (question, scaffold, worked parallel example).
4. Records every decision, with its reasons, as nodes and edges.

After the session, a consolidator folds what happened into that child's long-term graph. Next session, the plan and the hints differ because of that memory. A **Why panel** shows the live graphs and the path behind each decision.

**Inspiration:** the Primer in Neal Stephenson's *The Diamond Age*. We build one narrow slice of that idea (adaptive early arithmetic with memory that changes teaching), not the whole vision.

**Honest limits:** no real-child testing has been done. We make no claim that this improves learning. The contribution is an architecture in which a graph decides, remembers and explains.

---

## 2. Hackathon compliance map

| Rule | How Primer satisfies it |
|---|---|
| 2. FalkorDB primary graph DB, central to product | All planning, diagnosis, memory and traces run as Cypher on FalkorDB. No other datastore holds state. |
| 3. Graph must do real work | Section 7.6: a **Graph off** toggle degrades the tutor to a generic one. The diagnosis (variable-length traversal), frontier selection, hint-style memory and decision provenance are graph queries. |
| 4. Run FalkorDB any way | Docker locally, Docker on one AWS EC2 box for deploy. |
| 5. Name tracks | **Track 02 Agent Memory and Coordination (primary)**, **Track 01 Agents That Act on Connected Data (secondary)**. |
| 6. Allowed data | Synthetic personas only. |
| 8. Work starts after kickoff | Repo is created and committed after Oct 15, 12:01 AM IST. Commit history shows it. |
| 10. Submission contents | Public repo, README with data model, `docs/QUERIES.md`, demo video, deployment or local setup, track named. Checklist in section 15. |
| 11. AI disclosure | README section "How AI was used". |
| 12, 13. Understand the code | `docs/EXPLAIN.md` (section 14, phase 7) explains each key query and engine in plain English. |

Track fit, stated precisely:

- **Track 02:** per-child isolated graphs (one graph per tenant), episodic memory (Episodes), semantic memory (skill confidence, interests), procedural memory (which hint styles work for this child), working memory (session graph), and a handoff between Assessor, Planner, Tutor and Consolidator that happens **only through the graph**.
- **Track 01:** multi-hop traversal as a decision tool, graph queries as agent tools, explainable results (Decision nodes with `BECAUSE` edges). MCP exposure is a stretch goal (phase 8).

---

## 3. Scope

### In
- Arithmetic only: 13 skills, ages 5 to 7.
- 3 synthetic personas: Leo, Meera, Arjun.
- Child view, Why panel, demo controls, BYOK settings.
- Deterministic answer checking, misconception rules, planner, mastery update, consolidation.
- LLM used only for wording (hints, story frame, episode summary), with validators and template fallbacks.
- A **Graph off** ablation toggle.
- Docker Compose local run and single-box AWS deploy.
- Tests: pytest (unit and graph integration), Playwright end to end.

### Out (do not build)
Reading, writing, phonics, voice input, speech output, accounts, auth, payments, parent portals, multiple subjects, mobile apps, a custom curriculum editor, analytics, i18n, real child data.

### Stretch (only after phase 7 is fully done)
MCP server exposing graph tools (phase 8). Browser text-to-speech for the tutor bubble.

---

## 4. The demo script (acceptance test for the whole product)

This is the story the video tells. Phase 6 turns it into an automated Playwright test.

**Setup:** `POST /api/demo/reset` re-seeds the three personas. Leo (6, loves space) has strong counting skills and a weak `count_on` (confidence 0.35).

**Day 1, graph on**
1. Pick Leo. The planner selects `count_on` (the frontier skill). The Why panel shows a Decision: chose `count_on` because `count_20`, `one_more_less` are mastered and `count_on` has confidence 0.35.
2. First problem is scripted for the demo: **3 + 4** in a rocket story with 3 fuel cells loaded and 4 more to find.
3. Leo taps **6** (wrong). Assessor labels it `counts_start_number` (6 is one less than 7). A `diagnose` Decision appears, with the traversal path to the weak skill.
4. Hint level 1, style `story` (first by default order). Leo taps **6** again (wrong).
5. Hint level 2, style `visual` (the second-ranked style). Leo taps **7** (correct, after hints).
6. The tutor asks one reflective question ("How did you get it?"). Leo may type anything or skip.
7. Leo finishes a few more problems. Presses **End session**.
8. Consolidation runs. The Why panel shows a memory diff: `count_on` confidence before and after, a new Episode node, hint-style scores changed (`story` down, `visual` up), the exhibited misconception recorded.

**Day 2, graph on**
9. Press **Next day**. Same child, new session. The planner's decision cites the Episode from Day 1. The first hint style is now `visual`, with the reason "worked last session". The story still uses Leo's interests.

**Ablation**
10. Switch **Graph off**, start a session. The tutor is generic: no interests, no diagnosis, no history, random next problem. The panel says "graph disabled". Switch back on to show the difference.

**Pass criteria:** every step above works end to end with the fake LLM (deterministic) and with a live LLM.

---

## 5. Architecture

```
Browser (Next.js)
  Child stage            Why panel                 Demo bar
     |                      |                         |
     +----------- REST (JSON) over HTTPS ------------+
                           |
                    FastAPI backend
   +------------+   +-----------+   +------------+   +--------------+
   | Assessor   |   | Planner   |   | Tutor      |   | Consolidator |
   | (rules)    |   | (Cypher)  |   | (LLM words)|   | (code + LLM) |
   +-----+------+   +-----+-----+   +-----+------+   +------+-------+
         |                |               |                 |
         +----------------+---- graph ----+-----------------+
                           |      only
                      FalkorDB
          curriculum  |  child_<id>  |  session_<id>
```

### 5.1 Components and responsibilities

| Component | LLM? | Job |
|---|---|---|
| **Assessor** | No | Checks the answer in code. Classifies misconception with rules. Writes the Turn to the session graph. |
| **Planner** | No | Reads the session graph. Runs diagnosis, frontier and hint-style queries. Decides advance, hint, regress or return. Writes Decision nodes. |
| **Tutor** | Yes (words only) | Turns a structured hint plan into 1 to 2 short child-friendly sentences. Never receives the correct answer. |
| **Consolidator** | Partly | Folds the session graph into the child graph in code. The LLM only writes a short episode summary, with a template fallback. |

The agents communicate **only** by reading and writing the graph. There is no shared in-memory state between them beyond a single request.

### 5.2 The three context graphs, defined

| Context graph | Where | Role |
|---|---|---|
| **Short-term (working memory)** | `session_<id>` | Snapshot of the child's skills at session start, plus Turns and live Decisions. Exists only for the session. |
| **Long-term (memory)** | `child_<id>` | Skills with confidence, Interests, Episodes, hint-style effectiveness, historical Decisions. One graph per child. |
| **Reasoning (trace)** | `Decision` nodes with `BECAUSE` edges, in the session graph while live, copied to the child graph at consolidation | Why the system chose what it chose. |

`curriculum` is a template graph that is **copied** into each child graph and session graph. Do not rely on queries across graphs.

### 5.3 Hydrate and consolidate (the memory pattern)

- **Session start (hydrate):** read the child graph, create `session_<id>`, copy in the Skill DAG with current confidences, Misconception links, HintStyle scores and Interests.
- **During session:** all reads and writes touch only the session graph.
- **Session end (consolidate):** merge working state back into the child graph, create an Episode, copy Decisions, delete the session graph.

---

## 6. Graph data model

### 6.1 Curriculum (13 skills)

| order | id | name | prerequisites |
|---|---|---|---|
| 1 | `count_10` | Counting to 10 | none |
| 2 | `count_20` | Counting to 20 | `count_10` |
| 3 | `one_more_less` | One more, one less | `count_20` |
| 4 | `bonds_5` | Number bonds to 5 | `count_10` |
| 5 | `count_on` | Counting on | `count_20`, `one_more_less` |
| 6 | `add_5` | Addition within 5 | `bonds_5`, `count_on` |
| 7 | `sub_5` | Subtraction within 5 | `add_5` |
| 8 | `bonds_10` | Number bonds to 10 | `bonds_5`, `count_20` |
| 9 | `add_10` | Addition within 10 | `add_5`, `bonds_10` |
| 10 | `sub_10` | Subtraction within 10 | `sub_5`, `add_10` |
| 11 | `doubles` | Doubles | `add_10` |
| 12 | `make_ten` | Making ten | `bonds_10`, `add_10` |
| 13 | `add_20` | Addition within 20 | `make_ten`, `doubles` |

Store as Python data in `backend/app/graph/seed.py`. Edge direction: `(prereq)-[:PREREQUISITE_OF]->(skill)`.

### 6.2 Misconceptions (rules, section 7.2)

| id | name | indicates weak |
|---|---|---|
| `counts_start_number` | Counts the starting number as one of the steps | `count_on` |
| `overshoots_by_one` | Counts one too many | `one_more_less` |
| `adds_instead_of_subtracts` | Adds when asked to take away | `sub_5` |
| `subtracts_instead_of_adds` | Takes away when asked to put together | `add_5` |
| `reports_an_addend` | Answers with one of the numbers given | `bonds_5` |

Anything unmatched is recorded as `unclassified`. There is no sixth rule. Never invent a diagnosis.

### 6.3 Node and edge catalogue

**Template graph `curriculum`**
- `(:Skill {id, name, order})`, `(:Misconception {id, name})`
- `(:Skill)-[:PREREQUISITE_OF]->(:Skill)`, `(:Misconception)-[:INDICATES_WEAK]->(:Skill)`

**Long-term graph `child_<id>`** (adds to the template copy)
- `(:Child {id, name, age})`
- `(:Skill {id, name, order, confidence, attempts, last_seen})`
- `(:Interest {name})`, `(:Child)-[:INTERESTED_IN {weight}]->(:Interest)`
- `(:HintStyle {id, order, score, tries})` for `story`, `visual`, `question`, `physical`. Default order: story, visual, question, physical. Default score 0.5, tries 0.
- `(:Episode {id, ts, session_id, correct, total, hints_used, summary})`, `(:Child)-[:HAD]->(:Episode)`
- `(:Episode)-[:PRACTICED {before, after}]->(:Skill)`
- `(:Episode)-[:EXHIBITED {count}]->(:Misconception)`
- `(:Episode)-[:USED_STYLE {tries, helped}]->(:HintStyle)`
- `(:Decision {id, ts, kind, summary, memory_used, session_id})` with `[:CHOSE]->(:Skill|:HintStyle)` and `[:BECAUSE {role}]->(:Skill|:Misconception|:Episode)`

**Short-term graph `session_<id>`**
- `(:Session {id, child_id, started_at, graph_mode, turn_count, target_skill, origin_skill})`
- Working copies of `Skill` (with `confidence`), `PREREQUISITE_OF`, `Misconception`, `INDICATES_WEAK`, `HintStyle` (with scores), `Interest`.
- `(:Turn {n, problem_id, skill_id, op, a, b, answer, given, correct, misconception_id, hint_level, hint_style, ts})`
- `(:Session)-[:HAS_TURN]->(:Turn)`, `(:Turn)-[:NEXT]->(:Turn)`
- `(:Decision ...)` as above; `BECAUSE` may point to `Turn`, `Skill`, `Misconception`.

`kind` values for Decision: `select_skill`, `diagnose`, `hint`, `regress`, `return`, `advance`.
`memory_used` is a list of any of: `working`, `semantic`, `episodic`, `procedural`. The Why panel shows it.

### 6.4 Synthetic personas

| Persona | Age | Interests | Starting confidences |
|---|---|---|---|
| Leo | 6 | space, rockets | `count_10` 0.95, `count_20` 0.90, `one_more_less` 0.85, `bonds_5` 0.85, `count_on` 0.35, `add_5` 0.60, rest 0.0 |
| Meera | 5 | dinosaurs | `count_10` 0.70, `count_20` 0.30, rest 0.0 |
| Arjun | 7 | cricket | `count_10` through `add_10` 0.85 or higher, `sub_10` 0.45, `doubles` 0.30, rest 0.0 |

Each persona also has an optional `opening_problem` for scripted demos. Leo's is `3 + 4` on `count_on`.

---

## 7. Engines

### 7.1 Problem generator (`engines/problems.py`)
Deterministic, seeded by `(child_id, session_index, turn_n)`. Returns `{problem_id, skill_id, op, a, b, answer, story_slots}`.

| skill | problem shape |
|---|---|
| `count_10`, `count_20` | "How many?" with N objects, N within range |
| `one_more_less` | "One more than X" or "one less than X" |
| `bonds_5`, `bonds_10` | "A and ? make T", `op='?'`, answer T minus A |
| `count_on` | `a + b` with a from 2 to 9, b from 2 to 5 |
| `add_5`, `add_10`, `add_20` | sums within 5, 10, 20 |
| `sub_5`, `sub_10` | `a - b`, a within range, b less than a |
| `doubles` | `a + a`, a up to 10 |
| `make_ten` | `a + b` with sum 11 to 18 |

`parallel_problem(problem)` returns a problem of the same shape where **no operand and no result equals the original answer**. Used for level 3 worked examples.

### 7.2 Assessor rules (`engines/assessor.py`)
Inputs: `op, a, b, answer, given`. If `given == answer`, correct. Else first matching rule wins:

1. `op == '+'` and `given == answer - 1` -> `counts_start_number`
2. `op == '+'` and `given == answer + 1` -> `overshoots_by_one`
3. `op == '-'` and `given == a + b` -> `adds_instead_of_subtracts`
4. `op == '+'` and `given == abs(a - b)` -> `subtracts_instead_of_adds`
5. `op == '+'` and `given in (a, b)` -> `reports_an_addend`
6. otherwise `unclassified`

Rule order matters for ties. Parametrized unit tests must pin every rule and every tie.

### 7.3 Mastery update (`engines/mastery.py`)
Per skill, `confidence` in [0, 1]. Applied to the **skill of the problem**, in the session graph, after every attempt.

- correct, hint level h: `c = c + (1 - c) * gain[h]`, with `gain = [0.35, 0.18, 0.10, 0.05]` for h = 0, 1, 2, 3
- wrong: `c = c - c * 0.20`
- clamp to [0, 1]

Thresholds: **weak** below 0.5, **mastered** 0.8 or higher. State plainly in the README that this is a simple explainable heuristic, not a validated psychometric model.

### 7.4 Planner (`engines/planner.py`)

Decision logic after each attempt:

1. **Correct**
   - If the skill's working confidence is 0.8 or higher: `advance` to the frontier skill (Q3).
   - Else: new problem on the same skill.
   - If currently regressed and the regress skill has 2 consecutive correct: `return` to `origin_skill`.
2. **Wrong**
   - Run Q2 (diagnose) and write a `diagnose` Decision, citing the matched misconception (or `unclassified`) and the traversal path.
   - Hint level 1, 2 or 3 per the ladder (7.5), choose style per Q4, write a `hint` Decision.
   - If the 4th attempt on the same problem is wrong: `regress` to the diagnosed weak ancestor and set `origin_skill`. If Q2 returns no weak ancestor, serve an easier problem on the same skill (smaller numbers) and record that no ancestor was weak.

Hint style choice (Q4): level 1 uses the top-ranked style, level 2 uses the second-ranked, level 3 uses the top-ranked again. Rank by `score DESC, tries ASC, order ASC`.

### 7.5 Hint ladder
- **Level 1:** a single guiding question. Never states or implies the answer.
- **Level 2:** a concrete scaffold (count the objects, use fingers, jump along a number line). Still no answer.
- **Level 3:** a worked parallel example with different numbers (`parallel_problem`), then the original question again.
- **After the 4th wrong:** regress (7.4).

The correct answer is **never** shown to the child as text from the tutor.

### 7.6 Graph-off ablation
When `graph_mode = off`: no hydration beyond a bare session; the tutor gets no interests, no misconception, no prerequisite path, no hint-style ranking; next problem is random within a fixed easy range. Decisions are not written. The Why panel shows "graph disabled". This exists to demonstrate Rule 3 honestly. It is a demo control, not a proof of effectiveness.

### 7.7 Consolidator (`graph/consolidate.py`)
Deterministic steps in one function:

1. Read all Turns and the working Skill confidences from `session_<id>`.
2. Write confidences back to `child_<id>` Skills. Update `attempts` and `last_seen`.
3. Create an Episode with `correct`, `total`, `hints_used`. Link `PRACTICED {before, after}`.
4. Link `EXHIBITED {count}` per misconception seen.
5. Hint-style learning: for each wrong turn followed by a hint of style S and then a correct next turn on the same problem, `helped = 1`, otherwise 0. Update `tries += 1` and `score = 0.7 * score + 0.3 * helped_rate` for that style. Link `USED_STYLE`.
6. Copy Decision nodes and their `BECAUSE` and `CHOSE` edges into the child graph. Map `Turn` targets to the new Episode. Map Skill and Misconception targets by `id`.
7. Optional LLM episode summary, 2 to 3 plain sentences from structured stats. Template fallback if it fails or violates validators.
8. Delete `session_<id>`.
9. Return a diff for the UI: per-skill before and after, new Episode, style score changes.

If any step fails, the session graph is **not** deleted. Consolidation must be re-runnable (idempotent on Episode id).

---

## 8. LLM layer

### 8.1 Provider interface (`llm/client.py`)
One function: `chat(messages, max_tokens, temperature) -> str`. Implemented over OpenAI-compatible `/chat/completions` using `httpx`.

- **Provider allowlist** (prevents server-side request forgery from user-supplied URLs). Only these base URLs are accepted. Verify each in the first hour:
  - `groq`: `https://api.groq.com/openai/v1`
  - `openrouter`: `https://openrouter.ai/api/v1`
  - `gemini`: `https://generativelanguage.googleapis.com/v1beta/openai/`
  - `openai`: `https://api.openai.com/v1`
- The request carries `provider`, `model` and key. **Never** accept an arbitrary base URL.
- Defaults come from env: `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`. Model names change often, so the human sets them after testing.
- **BYOK:** the browser sends the key in a request header per call. The backend never logs, stores or echoes it. Redact it in error handling.
- Timeout 6 seconds, one retry, then template fallback. In-memory LRU cache keyed by prompt hash. Per-IP rate limit (30 requests a minute).
- `LLM_MODE=fake` selects a deterministic fake client used in tests, CI and as an emergency demo mode.

### 8.2 Tutor prompt contract
The system prompt states: you speak to a child aged `{age}`; reply in **at most 2 sentences and 25 words**; use short, simple words; ask **exactly one** question; be warm; never say "wrong" or "incorrect"; never state or hint at the final answer; use the interest `{interest}` in the story.

The user message is structured JSON containing: child first name, interests, problem text, the **wrong answer given** (not the correct one), misconception id or `unclassified`, hint level, hint style, weak prerequisite name, and for level 3 the parallel problem with its worked solution.

**The correct answer is never sent to the model.** That makes leaking it impossible by construction.

### 8.3 Validators (`llm/validators.py`)
Reject and regenerate once, then use a template, if the output:
- contains the original correct answer as a whole-token digit or number word (for 7: "7", "seven"; do not match inside "17")
- exceeds 25 words or 2 sentences
- contains words from a banned list (`wrong`, `incorrect`, `fail`, `bad`, `stupid`)
- has more than one question mark
- is empty

Level 3 outputs may contain the parallel example's numbers. `parallel_problem` guarantees none equals the original answer.

### 8.4 Templates (`llm/templates.py`)
At least one generic template per (style, level) pair: 4 styles x 3 levels = 12. Plus 3 for `counts_start_number`. Placeholders: child name, object noun, numbers from the problem (never the answer). Templates must pass the same validators. There is a unit test that checks every template.

### 8.5 Story frame
Each problem gets a 1 to 2 sentence story frame from the LLM (fallback: template) using the child's interest and the persona's object set (rocket fuel cells, dinosaur eggs, cricket balls). Objects are drawn from custom SVG assets (section 10.3), not emoji.

---

## 9. API

All JSON. Prefix `/api`. Use sync (`def`) FastAPI endpoints with the sync `falkordb` client unless there is a clear reason otherwise.

| Method and path | Purpose |
|---|---|
| `GET /api/health` | Backend and FalkorDB reachable |
| `GET /api/children` | List personas with starting summary |
| `POST /api/demo/reset` | Re-seed all personas, delete all `session_*` graphs |
| `POST /api/sessions` | Body: `{child_id, graph_mode}`. Hydrates, returns `{session_id, problem, story}` |
| `POST /api/sessions/{id}/answer` | Body: `{problem_id, given, free_text?}`. Returns `{correct, kind, tutor_text, next_problem?, decision_ids[], working_confidence}` where `kind` is `praise`, `hint`, `regress`, `advance` or `return` |
| `POST /api/sessions/{id}/end` | Consolidates. Returns the memory diff |
| `GET /api/sessions/{id}/graph` | Nodes and edges of the session graph for the viewer |
| `GET /api/children/{id}/graph` | Nodes and edges of the long-term graph |
| `GET /api/children/{id}/decisions` | Decision history |
| `GET /api/decisions/{id}/path` | Nodes and edges that justify one decision, for highlighting |

Request headers for LLM settings: `X-LLM-Provider`, `X-LLM-Model`, `X-LLM-Key` (all optional; env defaults apply).

Errors are JSON `{error, detail}` with correct status codes. Validate with Pydantic. CORS limited to the configured frontend origin.

---

## 10. Frontend

Next.js (App Router) and TypeScript, Tailwind v4, Motion (`motion/react`), `@phosphor-icons/react` for icons, `react-force-graph-2d` for graphs (client-only dynamic import). Install commands are verified against `package.json` before use.

### 10.1 Screens
1. **Persona picker** (`/`): "Who is learning today?" Three personas. A discreet link to Settings (BYOK).
2. **Session** (`/learn/[sessionId]`): the **child stage** on the left and the **Why panel** on the right (collapsible). The **demo bar** is a thin strip, visually distinct from the child's area, with: day label, **End session**, **Next day**, **Graph on/off**, **Reset demo**.

### 10.2 Child stage
- One problem per screen. Story frame (1 to 2 short sentences), an object field drawn in custom SVG, a **number pad** (0 to 20 as needed). No typing for answers.
- Tutor bubble with the hint text. An optional "How did you get it?" text box after a correct answer.
- Quiet progress indicator (problems this session). **No timers, no streaks, no scores, no red error states, no confetti.** A wrong answer changes the tutor bubble, never the page chrome.
- Touch targets at least 56 px. High contrast. Large, plain type. Works on tablet width first, then desktop, then phone.
- Respect `prefers-reduced-motion`. Visible keyboard focus.

### 10.3 Object art
A small set of custom SVG illustrations in `frontend/public/objects/`: space set (rocket, star, fuel cell), dinosaur set (egg, footprint, leaf), cricket set (ball, bat, stump). Simple geometric shapes, consistent stroke and palette from `DESIGN.md`. These are illustrations, not icons. UI icons come from Phosphor only.

### 10.4 Why panel
- **Graph canvas** (force graph): nodes colored by memory type (working, long-term, reasoning). Legend included. Clicking a Decision highlights its `BECAUSE` path using `/api/decisions/{id}/path`.
- **Decision timeline:** each entry shows `kind`, one-line summary and `memory_used` tags.
- **Memory diff** after End session: skill confidence before and after, new Episode, hint-style score changes.
- When graph mode is off: a clear "graph disabled" state.
- Layout is tabbed or stacked, never cramped. Graph labels stay readable.

### 10.4.1 Plain-language rule
Every string the child sees is reading-level grade 1. Every string in the Why panel is plain English for a parent or judge. No jargon like "Cypher" in the UI.

### 10.5 Design direction (do not skip)
The UI must not look like generic AI output.

1. **Child stage** and **Why panel** are different surfaces with different jobs. Design them as one family (shared tokens for spacing and radii) with different personalities: warm and calm for the child, precise and instrument-like for the panel.
2. Follow the `frontend-design` skill's two-pass process: write a compact token plan, critique it against the brief, then build. Save the result as `docs/DESIGN.md` (colors as named hex values, type roles, layout notes, principles) **before** writing UI code.
3. Ground the design in the subject: a book-like, calm learning object for a 6-year-old. Do not default to the common tells listed in the `frontend-design` skill (cream plus terracotta, near-black plus acid accent, SaaS card kit, tracked-caps eyebrows everywhere).
4. Child-specific constraints in section 10.2 override any skill rule that conflicts (for example, large touch targets and generous spacing beat dense layouts).
5. Spend boldness in one place: the object field and the tutor bubble are the memorable part. Keep the rest quiet.
6. Quality floor: responsive, visible focus, reduced motion, accessible contrast, both light-only is acceptable (document the choice).

---

## 11. Testing

### 11.1 Backend (pytest)
- **Unit:** assessor rule table (every rule and every tie), mastery update (table of cases), problem generator (shape, seed determinism, `parallel_problem` guarantee), validators (leak, length, banned words), templates (all pass validators).
- **Graph integration** (needs a running FalkorDB, skipped with a clear message if absent): seed, hydrate, diagnose path, frontier selection, hint-style ranking, consolidation (confidences move, Episode exists, Decisions copied, session graph deleted), idempotent re-run.
- **API:** the full Leo day 1 then day 2 flow using `LLM_MODE=fake`, asserting that Day 2's first hint style is `visual` and that a Decision cites the Day 1 Episode.
- **Graph off:** asserts no Decision nodes are written and the tutor payload contains no interests or misconception.

### 11.2 Frontend and end to end
Use Playwright (Python) via the `webapp-testing` skill. Start servers with its `with_server.py` helper (run `--help` first). The E2E test follows section 4 exactly and saves screenshots to `e2e/screenshots/`. These screenshots are also used for the README and blog.

### 11.3 Definition of tested
A phase is done when its listed tests actually ran and passed in this environment. Print the test output in the phase report.

---

## 12. Deployment (AWS student credits)

The human has AWS builder student credits. Credit amount and eligible services are unknown to this spec. **Before launching anything:** check the credit balance, set a billing alarm, and plan to stop or terminate the instance after judging.

**Recommended: one EC2 instance, Docker Compose.** Pick the smallest instance class that runs three containers comfortably (a 2 GB RAM class is a reasonable starting guess; confirm in the console).

Containers: `falkordb`, `backend`, `frontend`, `caddy` (reverse proxy and automatic HTTPS).

- A free domain or subdomain pointed at the instance is needed for HTTPS (BYOK keys must not travel over plain HTTP). Use whatever the human prefers.
- **FalkorDB must not be reachable from the internet.** It has no auth by default. Keep it on the Docker internal network and do **not** publish port 6379. Security group inbound: 80 and 443 from anywhere, 22 from the human's IP only.
- Mount a Docker volume for FalkorDB data so restarts keep personas. `POST /api/demo/reset` restores a known state before judging.
- `docker-compose.yml` for local dev. `docker-compose.prod.yml` for the box, plus `Caddyfile`.
- Warm the stack just before judging. Free tiers and cold starts are real.

**Optional alternative:** frontend on Vercel, backend on EC2. Still needs HTTPS on the backend.

**Optional LLM via AWS:** Amazon Bedrock could serve a hosted model. Do **not** assume credits cover it, that the needed models are enabled in the chosen region, or that it speaks the OpenAI-compatible API. If the human wants it, add it as a separate provider behind the same `chat()` function. Default path stays free-tier OpenAI-compatible plus BYOK.

**Fallback if deploy fails:** the rules accept complete local setup instructions plus the demo video. Never let deployment block the submission.

---

## 13. Repository layout

```
primer/
  .agent/skills/            (copied skills, see MASTER_PROMPT.md)
  docs/
    SPEC.md  DESIGN.md  QUERIES.md  EXPLAIN.md  DEMO_SCRIPT.md
  backend/
    app/
      main.py  config.py  models.py
      graph/   client.py  seed.py  session.py  consolidate.py  trace.py
               queries/*.cypher
      engines/ problems.py  assessor.py  mastery.py  planner.py
      llm/     client.py  providers.py  prompts.py  validators.py
               templates.py  fake.py
      api/     children.py  sessions.py  graphview.py  demo.py
    tests/
    pyproject.toml (or requirements.txt)
  frontend/                 (Next.js app)
  e2e/                      (Playwright scripts, screenshots)
  docker-compose.yml  docker-compose.prod.yml  Caddyfile
  .env.example  README.md
```

Key queries live in `backend/app/graph/queries/*.cypher` and are the **only** place Cypher strings are defined. `docs/QUERIES.md` is generated from them.

---

## 14. Build phases and acceptance criteria

Work one phase at a time. At the end of each phase, print a report: what was built, files changed, tests run with real output, anything uncertain. Commit after each phase.

### Phase 0: Scaffold (target 1 hour)
Repo layout, `docker-compose.yml` with FalkorDB, backend health endpoint that pings FalkorDB, Next.js app boots, `.env.example`. Write `docs/DESIGN.md` using the design process in section 10.5 **now**, before any UI.
**Accept:** `docker compose up` brings FalkorDB and backend up; `GET /api/health` returns ok; `DESIGN.md` exists.

### Phase 1: Graph model and queries (target 3 hours)
`schema.py`, `seed.py` (curriculum, personas), template-to-child and template-to-session builders, Q1 to Q8 as `.cypher` files with a thin runner.
**Accept:** integration tests for seeding, diagnosis path, frontier selection and hint-style ranking pass against real FalkorDB. **STOP and give the human a plain-English walkthrough of every query before continuing.**

### Phase 2: Engines (target 3 hours)
`problems.py`, `assessor.py`, `mastery.py`, `planner.py`.
**Accept:** unit tests from 11.1 pass, including every assessor rule and tie.

### Phase 3: Sessions and consolidation (target 3 hours)
Hydrate, turn recording, Decision writing, consolidation with diff, idempotency.
**Accept:** graph integration tests for consolidation pass; the Leo flow without LLM (fake) produces the day 2 behavior. **STOP and give the human a walkthrough of hydrate, planner and consolidator.**

### Phase 4: LLM layer (target 2 hours)
`client.py`, provider allowlist, BYOK headers, prompts, validators, templates, fake client, cache, rate limit.
**Accept:** validator and template tests pass; with `LLM_MODE=fake` the full API flow passes; with a live key (if the human supplies one) a real call returns validated text. Confirm no key appears in logs.

### Phase 5: Frontend (target 6 hours)
Persona picker, child stage, number pad, object art, tutor bubble, demo bar, Why panel with graph canvas, decision timeline, memory diff, settings dialog.
**Accept:** the section 4 flow can be completed by hand in the browser with the fake LLM.

### Phase 6: Ablation and E2E (target 3 hours)
Graph on or off toggle, `POST /api/demo/reset`, Playwright test for section 4, screenshots.
**Accept:** the Playwright test passes headless and screenshots are saved.

### Phase 7: Ship (target 4 hours, start no later than Oct 18 morning)
AWS deploy, README (setup, **graph data model**, **the Cypher the product depends on**, tracks entered, AI disclosure), `docs/QUERIES.md`, `docs/EXPLAIN.md` (plain-English explanation of every key query, engine and design decision, for the human to study), `docs/DEMO_SCRIPT.md` (shot-by-shot video script from section 4).
**Accept:** the deployed URL passes a smoke check, or local setup instructions are complete and tested from a clean clone.

### Phase 8: Stretch (only if phases 0 to 7 are fully done)
Python MCP server exposing graph tools (`diagnose_skill`, `next_frontier`, `rank_hint_styles`, `get_child_memory`), built per the `mcp-builder` skill, listed in the README for Track 01.

---

## 15. Known risks and mitigations

| Risk | Mitigation |
|---|---|
| A skeptical judge says "a recursive SQL query does this" | The pitch is not scale. It is one uniform graph for working memory, long-term memory and reasoning provenance, with `BECAUSE` edges that make every decision traceable. Show the Graph off ablation and the Decision path. |
| Free LLM rate limits or outage mid-demo | The engine is deterministic. Templates and the fake client keep everything working. Pre-record the video. |
| LLM leaks the answer or writes at the wrong level | It never receives the answer. Validators and template fallback (section 8.3). |
| Misconception rules look thin | Six outcomes, all tested. Design demo problems to hit them. Say "unclassified" when unsure. |
| Unexplainable AI-written code | `docs/EXPLAIN.md`, phase STOP points, small files. |
| FalkorDB Cypher surprises | Verify every query in a real container. One `.cypher` file per query. Record fixes. |
| Deploy eats the last day | Deploy by midday Oct 18. Fallback is local setup plus video. |
| BYOK key leaks, SSRF, open database | Provider allowlist, no logging of keys, FalkorDB not published, security group locked down. |
| Time | Scope is binding. Phase 8 is the first thing cut. |

---

## 16. Submission checklist (Rule 10)

- [ ] Public GitHub repository
- [ ] README with setup instructions **and** the graph data model
- [ ] The Cypher queries the product depends on (`docs/QUERIES.md`, linked from README)
- [ ] Demo video showing the working project (follow `docs/DEMO_SCRIPT.md`)
- [ ] Live deployment URL, or complete local setup instructions
- [ ] Tracks named on the form: Track 02 primary, Track 01 secondary
- [ ] "How AI was used" section in README
- [ ] Blog post for the best-blog-post side prize (optional, strongly encouraged)
- [ ] Submitted before Oct 18, 11:59 PM IST. Aim for several hours early.
