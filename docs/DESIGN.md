# Primer — Design System

> This file is the source of truth for all visual decisions in Primer.
> It is written before any UI code and governs both surfaces.
> Child-safety constraints (section 10.2 of the spec) override every aesthetic choice below.

---

## 1. Two surfaces, one family

| Surface | Job | Personality |
|---|---|---|
| **Child stage** | One problem per screen. Child interacts here. | Calm, warm, book-like. Never alarming. |
| **Why panel** | Shows the graph, decisions, memory diff. For a parent or judge. | Precise, instrument-like, data-forward. |
| **Demo bar** | Meta controls: day label, session controls, graph toggle. | Clearly "outside" the child's world. Thin strip. |

They share spacing tokens and border-radius values. They do not share color or type roles.

---

## 2. Color

All values are named. Never use hex literals in component code — use CSS custom properties.

### Child stage palette

| Token | Hex | Role |
|---|---|---|
| `--cs-bg` | `#F7F4ED` | Page background. Warm off-white, like aged paper. |
| `--cs-surface` | `#FFFFFF` | Card / problem container. |
| `--cs-ink` | `#1A1A2E` | All text the child reads. Deep indigo-navy. Passes AA on both bg values. |
| `--cs-ink-soft` | `#4A4A6A` | Secondary text (story frame, quiet labels). |
| `--cs-structure` | `#7B9CB8` | Borders, dividers on the child side. Dusty blue. |
| `--cs-bubble` | `#F5C842` | Tutor bubble background. Warm amber-ochre. |
| `--cs-bubble-ink` | `#1A1A2E` | Text inside the tutor bubble. Same deep navy — passes AA on amber. |
| `--cs-numpad-bg` | `#EAE6DC` | Number-pad button resting state. |
| `--cs-numpad-hover` | `#D4CEBD` | Number-pad button hover. |
| `--cs-numpad-active` | `#7B9CB8` | Number-pad button pressed (dusty blue). |
| `--cs-numpad-ink` | `#1A1A2E` | Number-pad digit text. |
| `--cs-correct` | `#4C9A6A` | Quiet correct indicator (a soft green checkmark only, no splash). |
| `--cs-focus-ring` | `#2D6FAD` | Keyboard focus outline. Clear, not distracting. |

### Why panel palette

| Token | Hex | Role |
|---|---|---|
| `--wp-bg` | `#F0F2F5` | Panel background. Cool off-white. |
| `--wp-surface` | `#FFFFFF` | Card / section surface. |
| `--wp-ink` | `#1E2532` | All text in the panel. Dark slate. |
| `--wp-ink-soft` | `#5A6478` | Secondary / metadata text. |
| `--wp-border` | `#CDD2DB` | Visible dividers and grid lines. |
| `--wp-accent` | `#2D9CDB` | Graph node highlights, active decision, links. Clear teal. |
| `--wp-accent-dim` | `#A8D4EF` | Dim accent for inactive graph edges and low-confidence nodes. |
| `--wp-tag-working` | `#E8F4FD` / `#2D9CDB` | "Working memory" badge: pale teal fill, teal text. |
| `--wp-tag-episodic` | `#FEF3E2` / `#D97B22` | "Episodic memory" badge. |
| `--wp-tag-semantic` | `#EDF7ED` / `#2E7D32` | "Semantic memory" badge. |
| `--wp-tag-procedural` | `#F3E8FD` / `#7B2FBE` | "Procedural memory" badge. |

### Demo bar palette

| Token | Hex | Role |
|---|---|---|
| `--db-bg` | `#1E2532` | Strip background. Same as `--wp-ink` — clearly meta. |
| `--db-ink` | `#E0E4EC` | Text and labels in the demo bar. |
| `--db-accent` | `#F5C842` | Active state highlight (same amber as tutor bubble — links the two worlds). |
| `--db-border` | `#3A4154` | Dividers inside the demo bar. |

---

## 3. Typography

Two families. Clear distinction between surfaces.

### Families

| Family | Usage |
|---|---|
| **Nunito** (Google Fonts) | Child stage — all text the child sees. Rounded, friendly. Weights: 400, 600, 700. |
| **Nunito Sans** (Google Fonts) | Why panel prose, labels, narrative text. More neutral than Nunito but from the same superfamily. Weights: 400, 600. |
| **IBM Plex Mono** (Google Fonts) | Why panel tabular data, confidence values, node IDs, Cypher query display. Weight: 400 only. |

### Type scale

| Role | Family | Size | Weight | Line-height | Where |
|---|---|---|---|---|---|
| `--t-story` | Nunito | 1.5rem (24px) | 600 | 1.5 | Story frame (child reads) |
| `--t-question` | Nunito | 2rem (32px) | 700 | 1.3 | Problem question text |
| `--t-bubble` | Nunito | 1.375rem (22px) | 600 | 1.45 | Tutor bubble text |
| `--t-numpad` | Nunito | 1.75rem (28px) | 700 | 1 | Number pad digits |
| `--t-reflective` | Nunito | 1.125rem (18px) | 400 | 1.6 | "How did you get it?" label |
| `--t-wp-label` | Nunito Sans | 0.75rem (12px) | 600 | 1 | Why panel field labels, ALL UPPERCASE only here |
| `--t-wp-body` | Nunito Sans | 0.875rem (14px) | 400 | 1.55 | Why panel prose |
| `--t-wp-heading` | Nunito Sans | 1rem (16px) | 600 | 1.3 | Why panel section headings |
| `--t-data` | IBM Plex Mono | 0.8125rem (13px) | 400 | 1.4 | Confidence values, node IDs |
| `--t-db-label` | IBM Plex Mono | 0.75rem (12px) | 400 | 1 | Demo bar labels |

Line length: prose in Why panel ≤ 65ch. Child stage question ≤ 20ch (one thought per line).

---

## 4. Spacing and layout

Base unit: **8px**. All spacing is a multiple of 8.

| Token | Value | Role |
|---|---|---|
| `--space-xs` | 4px | Icon gap, tight pairs |
| `--space-s` | 8px | Within a component |
| `--space-m` | 16px | Between sibling components |
| `--space-l` | 24px | Section gaps |
| `--space-xl` | 40px | Major layout breaks |
| `--space-2xl` | 64px | Top-of-page breathing room |

### Layout

- **Tablet first** (768px base). Desktop widens the gutter. Phone collapses Why panel to a drawer.
- Child stage: centered column, max-width 560px, generous vertical padding (`--space-2xl` top).
- Why panel: 340px wide at tablet, 400px at desktop. Fixed right, scrollable internally.
- Demo bar: 48px tall strip pinned at top, full width. `z-index` above both panels.
- Object field: a 240 × 180px SVG canvas on tablet, up to 320 × 240px on desktop.

---

## 5. Border radius

| Token | Value | Used on |
|---|---|---|
| `--radius-s` | 6px | Why panel tags, badges |
| `--radius-m` | 12px | Cards, number-pad buttons |
| `--radius-l` | 20px | Tutor bubble |
| `--radius-full` | 9999px | Pill buttons (End session etc.) |

---

## 6. Touch targets and accessibility

- Every interactive element: min 56 × 56px (spec requirement).
- Number pad buttons: 72px square on tablet.
- Visible focus ring using `--cs-focus-ring` (3px solid, 2px offset) on all focusable elements.
- `prefers-reduced-motion`: all `motion/react` animations are gated. Static state is always correct without motion.
- Contrast: all text / background pairs target WCAG AA (4.5:1 minimum). Deep navy on warm white = 15:1. White on amber bubble = check — `#1A1A2E` on `#F5C842` ≈ 8.5:1. ✓

---

## 7. Iconography

- UI icons: **Phosphor Icons** only. One family, one stroke weight (`regular`, 24px).
- Illustrations (object field): custom SVG files in `frontend/public/objects/`. Not emoji.
- Three sets: space (rocket, star, fuel cell), dinosaur (egg, footprint, leaf), cricket (ball, bat, stump).
- Illustration style: simple geometric shapes. Stroke: 2.5px, rounded caps/joins. Colors from child palette (`--cs-structure`, `--cs-bubble`, `--cs-correct`).

---

## 8. Motion

`MOTION_INTENSITY: 3` for child stage. `MOTION_INTENSITY: 2` for Why panel.

- Child stage: the tutor bubble **slides in** from below when it first appears (100ms ease-out). Wrong answer: bubble content crossfades to new text (80ms). Correct: a quiet pulse on the bubble border (one cycle, not looped). No confetti. No timers. No red flash.
- Why panel: graph nodes fade in on first load (200ms stagger). Decision timeline entries slide in from the right as they appear.
- Demo bar: no motion beyond button press states.
- All animations are wrapped in `@media (prefers-reduced-motion: reduce)` guard — they become instant when reduced motion is set.

---

## 9. Principles (what makes this design specific to this brief)

1. **The page is a book, not an app.** No dashboard chrome on the child stage. No sidebars, toolbars, or notification areas. One thing at a time.
2. **Boldness is spent on the object field and the tutor bubble.** Everything else — the number pad, the story text, the progress dot — is quiet and subservient.
3. **Wrong answer → tutor responds, nothing else changes.** The page chrome (background, layout, header) must not react. Only the bubble content changes.
4. **The Why panel is a precision instrument.** It is allowed to be dense (for a parent/judge), but never jargon-heavy. No word "Cypher" appears in the UI. Teal accent is used sparingly and only for decision/highlight states.
5. **Demo bar is visually outside the child's world.** Dark background, monospace labels, clearly "meta". A child who sees it knows it is not part of the game.

---

## 10. What we are NOT doing (anti-patterns)

- No cream + terracotta palette.
- No acid-green on near-black.
- No SaaS card kit (uniform rounded-card grid for everything).
- No tracked-all-caps eyebrow labels on the child stage.
- No confetti, streaks, score counters, or timers visible to the child.
- No red error states visible to the child.
- No emoji in the object field — only custom SVG.
- No multiple icon families.
- No arbitrary colors for graph nodes — only the four memory-type tokens above.
