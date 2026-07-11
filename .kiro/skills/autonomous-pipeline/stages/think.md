# Stage ② THINK — Research & Alternatives

> The first stage allowed to propose a *fix* (the wall between EVALUATE's PRESENT-claim
> and THINK's plan). Explore approaches, surface risk, recommend a direction.

## Purpose
Turn a GO into a defensible direction. Not "pick the obvious"; generate real
alternatives under explicit constraints and falsify your own assumptions before PLAN.

## Mechanics

1. **Constraint-Driven Alternatives (T2, ≥2 required)** — generate approaches using
   explicit constraints, NOT generic Minimal/Ideal/Creative:
   `SPEED · QUALITY · SIMPLICITY · FLEXIBILITY · DELETION`.
   For each: name, the constraint it optimizes, the cost tradeoff it accepts.
   The "DELETION" lens is mandatory to consider — can the requirement be met by removing
   code / doing nothing structural?

2. **Design Risk Probe (T1, ≥3 required)** — self-answering probes that verify or
   falsify assumptions **without user interaction**. A probe reads code / runs a check /
   traces a path and records the answer. "Does NFKD decompose ß?" → "no, needs pre-map"
   is a probe. A probe with no answer is not a probe.

3. **MeshClaw code intel** — use CodeLens `find_callers` / `find_route` to ground probes
   about "how does the current system actually work" against real file:line, not memory.

4. **Minimum Depth Gate (BLOCKING)** — ≥2 alternatives + ≥3 resolved probes + stated
   cost tradeoffs. If <50% probes resolved AND high-stakes → escalate to an interactive
   grill (max 5 questions). Otherwise self-answer and proceed.

## Blocking Gates
Minimum depth gate (CLI checks `alternatives`, `risk_probe`, `recommendation` present).

## Output artifact (`publish --stage think`)
```json
{
  "alternatives": [
    {"name":"…","tradeoff":"SIMPLICITY: … accepts …"},
    {"name":"…","tradeoff":"FLEXIBILITY: … accepts …"}
  ],
  "risk_probe": [
    {"probe":"falsifiable question","answer":"resolved by reading X / running Y"}
  ],
  "recommendation": "chosen approach + why it beats the alternatives",
  "sources": ["file:line / doc refs consulted"]
}
```

## Common rationalizations → reality
- "One approach is obviously right" → generating a real alternative is how you discover
  the obvious one is wrong. 2 minutes.
- "I'll probe it during BUILD" → an unfalsified assumption that breaks in BUILD costs a
  micro-replan; falsifying it here costs a grep.
- "Deletion doesn't apply" → it applies more often than you think; the cheapest code is
  the code you didn't write.
