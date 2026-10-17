# MentoAI: Technical Explanation & Judge Q&A (30 Questions)

This document prepares the team to answer any architectural, algorithmic, or graph query questions during judging for **Graph Hacks: Context for AI Agents**.

---

### 1. What makes MentoAI different from a typical LLM chatbot?
A chatbot has transient context windows. MentoAI stores all facts, misconceptions, interests, entities, and teaching moves as durable nodes and edges in a FalkorDB graph. Every answer is guided by multi-hop graph traversals (G3 bridge paths, G4 weak prerequisites) and every decision is stored as a traceable path (`BECAUSE` provenance edges) that can be inspected in the Why Panel.

### 2. Which track are you submitting to?
Primary: **Track 02 (Agent Memory and Coordination)**. All agents (Triage, Companion, Listener, Cartographer, Strategist, Reflector, Guardian) communicate strictly through the FalkorDB graph.  
Secondary: **Track 01 (Connected Data and Reasoning Traces)**. Every pedagogical move is justified by multi-hop graph paths.

### 3. How do your agents coordinate?
They do not call each other directly or exchange message bus payloads. They coordinate by reading and writing graph state:
- The Listener writes `Evidence` and `Curiosity` nodes.
- The Cartographer reads candidate concepts and writes `Concept` nodes and `PREREQUISITE_OF` edges.
- The Strategist reads bridge paths and writes `Plan` and `Decision` nodes with `BECAUSE` edges.
- The Companion reads the `Plan` and speaks.

### 4. How do you prove Hackathon Rule 3 (FalkorDB is indispensable)?
We built an explicit **Graph Off** switch (`GRAPH_MODE=off`) accessible via the UI and API (`POST /api/admin/graph-mode`). When toggled OFF, all graph queries return empty results and graph writes are stopped. MentoAI reverts to a generic chatbot with zero memory of yesterday's conversations, no ability to bridge to known interests, no prerequisite diagnosis, and an empty Why Panel.

### 5. Why did you choose FalkorDB over a relational or document database?
Relationships like `PREREQUISITE_OF`, `ANALOGOUS_TO`, and `BECAUSE` form deep directed cyclic graphs. Traversing variable-length paths (e.g. 1 to 5 hops upstream in G4 or finding shortest bridge paths in G3) requires recursive recursive joins in SQL that scale exponentially. In FalkorDB, path traversals execute in sub-millisecond graph matrix operations.

### 6. How is multi-tenancy handled in FalkorDB?
Each learner has an isolated graph named `learner_<learner_id>`. This ensures zero data leakage between learners, fast index lookups, and trivial O(1) graph drops for GDPR/privacy compliance (`forget_learner` G15).

### 7. How does the Hot Path achieve low voice latency?
The hot path executes only two concurrent operations before generating speech: Triage safety check and Context Assembly (G1 snapshot + G2 vector recall). Token streaming feeds a sentence chunker that triggers browser SpeechSynthesis as soon as the first sentence completes (~1.5s). Heavy extraction (Listener, Cartographer, Strategist) runs asynchronously on the cold path.

### 8. What is the register system?
MentoAI does not use age bands or ask for the user's age. The Listener observes vocabulary, sentence complexity, and abstraction comfort, writing a `register_text` and confidence to the `Learner` node. A 60-year-old learning fractions and a 6-year-old exploring the moon receive personalized register-adapted speech.

### 9. What is Query G3 (Bridge Paths) doing?
It finds the shortest path connecting a new target concept to concepts the learner already `KNOWS` or passions they `LOVE` via `[:PREREQUISITE_OF|ANALOGOUS_TO|PART_OF|TOUCHES*1..4]`. This enables natural callbacks like connecting buoyant forces to octopus physiology.

### 10. What is Query G4 (Weak Prerequisites) doing?
When a learner shows confusion about concept X, G4 traverses upstream prerequisites `(p)-[:PREREQUISITE_OF*1..5]->(target)` returning prerequisites with low depth or an active `Misconception`. MentoAI addresses the root confusion first.

### 11. What is Query G10 and G11 (Decision Trace & Provenance)?
G10 writes a `Decision` node with outgoing `[:BECAUSE]` edges pointing to the exact `Evidence`, `Turn`, `Interest`, or `Misconception` that prompted the action. G11 fetches this 1-hop neighborhood for the Why Panel.

### 12. How do you prevent hallucinated or invalid graph writes?
All agent outputs are validated against strict Pydantic schemas using `call_structured()`. If an agent produces invalid JSON, the runtime retries with a repair prompt. If that fails, it logs a `PipelineFault` node and drops the write rather than polluting the graph.

### 13. What is the role of the Cartographer agent?
When the user mentions an unfamiliar domain or concept, the Cartographer dynamically queries LLM knowledge, canonicalizes the concept, generates a 384-dimensional vector embedding, and links it into the learner's graph via `PREREQUISITE_OF` and `ANALOGOUS_TO` edges (G9).

### 14. What are the three synthetic demo personas?
- **Mira (7yo)**: Octopuses (3 hearts), dog Biscuit, buoyancy and water displacement.
- **Arjun (teen)**: Cricket analytics, probability, gambler's fallacy misconception.
- **Lakshmi (adult)**: Baking, sourdough hydration, fractions as parts of a whole.

### 15. How does Mode A voice work?
Mode A runs entirely in the browser using the Web Speech API (`SpeechRecognition` and `SpeechSynthesis`). It has zero server GPU cost, zero latency audio processing, and works natively in Chrome and Edge.

### 16. How does barge-in work?
When the user speaks while MentoAI is talking, the client sends a `barge_in` event over the WebSocket. The server cancels speech streaming and truncates the stored `Turn(role='mentoai')` text to what was actually spoken before the interruption.

### 17. How is child safety guaranteed?
Deterministic keyword checks and an ultra-fast Triage model classify every turn before speech is generated. If distress or self-harm is detected, MentoAI switches to "Care Mode", speaking with gentle validation and advising the user to talk to a trusted adult, without abruptly ending the call.

### 18. How do you protect user privacy (Rule 6)?
We never prompt for or store real PII (names, schools, addresses). The Guardian agent audits turns asynchronously and flags PII for redaction. Furthermore, the `POST /api/learners/{id}/forget` endpoint instantly drops the entire tenant graph from FalkorDB.

### 19. How does G13 handle duplicate concepts?
It computes cosine similarity between concept vector embeddings combined with name similarity. When similarity exceeds 0.92, the Reflector consolidates them using `merge_duplicate_concepts`.

### 20. How are embeddings generated without GPU or paid APIs?
We use `fastembed` with a lightweight multilingual ONNX model (`BAAI/bge-small-en-v1.5`) generating 384-dimensional dense vectors locally with CPU inference in ~4ms, with a deterministic fallback.

### 21. What is the Grown-Up Digest?
At the end of a session, the Reflector analyzes all conversation turns and graph writes to generate an adult digest: explored topics, demonstrated strengths, shaky areas to reinforce, and suggested hands-on offline activities.

### 22. What does G14 (Hubs & Clusters) do?
It identifies central concept hubs and connected clusters in the learner's knowledge graph to summarize their "learning worlds".

### 23. What are Open Loops (G6)?
Questions or cliffhangers that were left open at the end of a session. In the next session, the Strategist retrieves open loops to kick off a welcoming conversation callback.

### 24. What are the allowed teaching moves?
Analogy, story, socratic questioning, worked example, hands-on activity, retrieval practice, humor, visual card, silence, reframe.

### 25. What is the `show` tool?
The Companion can call `show(kind, payload)` to render visual artifacts on screen: SVG diagrams, concept maps, story cards, or number lines. All SVG strings are sanitized by the server before sending.

### 26. Can MentoAI work with multiple LLM providers?
Yes. The runtime is provider-agnostic, supporting OpenAI, Groq, OpenRouter, and Google Gemini through an allowlisted proxy with circuit breakers and fallback tiers.

### 27. What is FastMCP?
FastMCP is our Model Context Protocol server (`backend/app/mcp_server.py`) exposing 6 standardized tools so external AI agents can query and reason over MentoAI's FalkorDB graph memory.

### 28. What happens if an agent fails in the cold path?
Errors are caught, logged to a `PipelineFault` node in the graph, and the system continues. The next turn is unaffected.

### 29. How does MentoAI handle ethical dilemmas?
It explores them Socratically without imposing a preachy verdict, recording the learner's reasoning in a `Dilemma` node to revisit later.

### 30. What is the single biggest takeaway for judges?
MentoAI replaces fixed curricula and generic chatbots with a truly dynamic, lifelong companion whose memory, callbacks, and pedagogical strategies are permanently grounded in a FalkorDB knowledge graph.
