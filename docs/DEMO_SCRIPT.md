# MentoAI: 3-Minute Demo Recording Script

**Project:** MentoAI — Voice Companion Backed by FalkorDB Graph Memory  
**Target Video Duration:** 2 minutes 50 seconds  
**Demo URL:** `http://localhost:3000`

---

## Act 1: The Vision (0:00 – 0:40)

**[Visual: Main interface loading with dark-mode aesthetic, glowing Voice Orb, and Constellation Mind graph.]**

**Speaker:**
"This is MentoAI, inspired by the Young Lady's Illustrated Primer in Neal Stephenson's *The Diamond Age*.
Most AI tutors are chatbots with temporary memory and fixed, rigid curricula. MentoAI is different: it is a voice-first lifelong companion that learns with you over time. Anyone can talk to it about anything—from octopus hearts to fraction baking or cricket analytics.

What makes it MentoAI is **FalkorDB graph memory**. Everything it learns about you—what you understand, what confuses you, and your passions—lives in a dynamic graph. And every teaching decision MentoAI makes is written back as an explicit, traceable path through that graph."

---

## Act 2: Live Interaction & Memory Bridging (0:40 – 1:35)

**[Visual: Click on the 'Mira' persona. The Constellation Mind graph loads with concepts like Octopus Biology and Buoyancy.]**

**Speaker:**
"Here is Mira, a curious 7-year-old. Over the last two days, she talked about how octopuses have 3 hearts and swimming with her dog Biscuit. Notice the Constellation Mind Graph on the right showing her active concepts in FalkorDB.

Let's speak to MentoAI:"

**[Action: Click the glowing Voice Orb and speak aloud:]**  
*"Why does Biscuit float in the pool, but my toy metal boat sinks?"*

**[Visual: Voice Orb pulses from cyan to violet thinking ring, then emerald speaking wave. Live Subtitles stream both sides. Constellation Mind pulses `buoyancy` and `water_displacement`.]**

**MentoAI Speaks:**
*"Biscuit floats because his furry body and air in his lungs push enough water aside to keep him buoyant! Just like how octopuses glide in the sea. But that heavy toy boat sinks when water fills it up, making it too dense to float!"*

---

## Act 3: The Why Panel (Pedagogical Trace) (1:35 – 2:10)

**[Visual: Click on the Why Panel on the bottom right.]**

**Speaker:**
"How did MentoAI know to make that comparison?
Look at the Why Panel. This isn't just LLM hallucination—it's a multi-hop reasoning trace retrieved via Cypher from FalkorDB.
MentoAI executed Query G3: it found a shortest path between the new concept `buoyancy` and Mira's demonstrated understanding of `octopus_biology` from Day 1, citing her pet dog Biscuit. Every `BECAUSE` edge is preserved in the graph."

---

## Act 4: The Rule 3 Proof (Graph Off Toggle) (2:10 – 2:35)

**[Visual: Flip the prominent 'Graph: ON' switch in the top bar to 'Graph: OFF'.]**

**Speaker:**
"Hackathon Rule 3 requires proving that the graph is indispensable.
Watch what happens when we toggle **Graph Mode OFF**.
The graph memory is bypassed. Now let's ask the exact same question:"

**[Action: Speak aloud:]**  
*"Why does Biscuit float?"*

**[Visual: MentoAI gives a generic Wikipedia-style explanation without mentioning octopuses, without mentioning the pool, and the Why Panel stays empty.]**

**Speaker:**
"Without FalkorDB, MentoAI has no past, no personal connections, and no pedagogical trace. The graph is the mind of the companion."

---

## Act 5: Adult Digest & Privacy (2:35 – 2:50)

**[Visual: Click the 'Digest' button. The Grown-Up Digest modal opens.]**

**Speaker:**
"At the end of each session, MentoAI synthesizes an Adult Digest for parents and mentors: strengths demonstrated, concepts to reinforce, and hands-on offline activities.
And when you're done, a single click on 'Forget Me' executes Cypher Query G15, permanently wiping the tenant graph.

MentoAI: A tutor that remembers who you are becoming."
