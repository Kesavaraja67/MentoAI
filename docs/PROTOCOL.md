# MentoAI: Realtime WebSocket Protocol Specification

WebSocket Endpoint: `/ws/conversations/{conversation_id}`

---

## 1. Overview & Handshake

Communication between the browser and MentoAI occurs over a bidirectional JSON WebSocket.
Immediately upon connecting, the client issues a `hello` event to establish tenant identity and mode:

```json
{
  "type": "hello",
  "learner_id": "mira",
  "mode": "A"
}
```

---

## 2. Inbound Messages (Client -> Server)

### `transcript.partial`
Emitted continuously while the user is speaking aloud:
```json
{
  "type": "transcript.partial",
  "text": "Why does Biscuit..."
}
```

### `transcript.final`
Emitted when a speech segment is finalized (end of turn):
```json
{
  "type": "transcript.final",
  "text": "Why does Biscuit float in the pool but a toy metal spoon sinks?"
}
```

### `barge_in`
Emitted when the user interrupts MentoAI while speaking:
```json
{
  "type": "barge_in",
  "spoken_chars": 42
}
```

### `control`
Session lifecycle control:
```json
{
  "type": "control",
  "action": "end"
}
```

---

## 3. Outbound Messages (Server -> Client)

### `state`
Reflects MentoAI's active cognition state:
```json
{
  "type": "state",
  "state": "listening" | "thinking" | "speaking"
}
```

### `subtitle.person`
Updates the client UI with user's speech transcript:
```json
{
  "type": "subtitle.person",
  "text": "Why does Biscuit float?",
  "final": true
}
```

### `subtitle.mentoai`
Streams spoken words for MentoAI:
```json
{
  "type": "subtitle.mentoai",
  "delta": "Biscuit floats because his body pushes aside enough water to hold him up!",
  "sentence_id": "s_1"
}
```

### `tts.text`
Emits full sentences for client-side SpeechSynthesis (Mode A):
```json
{
  "type": "tts.text",
  "sentence_id": "s_1",
  "text": "Biscuit floats because his body pushes aside enough water to hold him up!"
}
```

### `viz.event`
Mirrors background graph activities in near real time:
- `pulse`: Highlights a concept currently involved in reasoning.
- `add_node`: Broadcasts a newly defined concept from the Cartographer.
- `trace`: Broadcasts Strategist pedagogical moves.
- `mind_refresh`: Full subgraph snapshot for Constellation Mind graph.

### `visual`
Rendered by the Visual Stage when the Companion calls the `show` tool:
```json
{
  "type": "visual",
  "id": "vis_123",
  "kind": "story_card",
  "payload": {
    "title": "Buoyancy & Displacement",
    "caption": "How water pushes back against floating objects.",
    "tags": ["buoyancy", "physics"]
  }
}
```

### `decision`
Provides the pointer ID for the Why Panel:
```json
{
  "type": "decision",
  "id": "turn_abc123",
  "summary": "socratic: Prompted learner to reason about water volume"
}
```
