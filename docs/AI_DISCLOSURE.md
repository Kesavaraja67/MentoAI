# AI Disclosure (Hackathon Rule 11 Compliance)

**Project:** MentoAI  
**Hackathon:** Graph Hacks: Context for AI Agents (WeMakeDevs × FalkorDB), Oct 15–18, 2026.

In compliance with Hackathon Rule 11, the team transparently discloses all AI tools and models utilized during development:

1. **Coding Assistant:**
   - **Antigravity (Gemini 2.5 Pro)**: Used for scaffolding file architectures, drafting Cypher queries, implementing Pydantic schemas, and designing the Next.js React UI.

2. **In-Product LLM Models:**
   - Fast Tier: `llama-3.1-8b-instant` (Groq) / `gemini-1.5-flash` / `gpt-4o-mini` (Triage safety gate and Listener evidence extraction).
   - Smart Tier: `llama-3.3-70b-versatile` (Groq) / `gemini-1.5-pro` / `gpt-4o` (Cartographer concept expansion, Strategist pedagogical planning, Reflector session consolidation).
   - Voice Tier: Streaming conversational responses adapted to estimated learner registers.

3. **Embedding Model:**
   - `fastembed` with `BAAI/bge-small-en-v1.5` (384-dimensional dense vectors, CPU ONNX inference).

All architectural decisions, graph schema designs, Cypher queries, safety constitutions, and core logic were thoroughly reviewed, validated, and documented by the team.
