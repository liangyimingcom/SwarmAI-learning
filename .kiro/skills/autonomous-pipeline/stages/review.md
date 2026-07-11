# Stage ⑤ REVIEW — Multi-Layer Quality Gate

> Catch integration wiring bugs, convention violations, security issues that self-review
> misses. Two phases with separate retry accounting.

## Phase 1 — Pre-Gate + Spec Compliance (serial)

1. **Litmus Pre-Gate (30s structural sanity)** — any of these = FAIL → rework to BUILD
   (max 2 litmus failures):
   - HF1 scaffold-only (no real logic) · HF2 AC coverage gaps ·
   - HF3 internal contradictions · HF4 missing error handling.

2. **Spec Compliance Gate (BLOCKING, fresh sub-agent — NOT self-review)** — `spawn_run`
   a sub-agent to verify AC → implementation mapping and classify each AC as
   MISSING / EXTRA / MISUNDERSTOOD. Verdict PASS / WARNING / BLOCK. BLOCK → rework to
   BUILD (max 2 spec blocks; 3rd → full escalation).

## Phase 2 — Parallel Fan-Out (conditional)
**Trigger:** >3 files OR >100 lines OR touches auth/data/infra. `spawn_run` up to 3
parallel sub-agents:
- **Code Quality** — RP1-RP40 checklist, integration trace, replace/move parity, depth/seam.
- **Security & Safety** — confidence-gated scan per file (1-10 + exploit scenario), wire
  test WR1-4.
- **UX & Test** — frontend only: discoverability, feedback states, escape handling, E2E trace.

Below the trigger threshold, Phase 2 is skipped and the Gate-2 adversarial in DELIVER is
the backstop.

## Output artifact (`publish --stage review`)
```json
{
  "litmus_gate": "PASS | FAIL: HFx …",
  "spec_compliance": {"verdict":"PASS|WARNING|BLOCK","ac_mapping":"…MISSING/EXTRA…"},
  "quality_findings": [{"pattern":"RPn","severity":"…","note":"…"}],
  "security_findings": [{"file":"…","confidence":1,"exploit":"…"}],
  "ux_findings": []
}
```

## Common rationalizations → reality
- "I already reviewed it while building" → self-review shares the builder's blind spot;
  the fresh sub-agent is the point.
- "Silence means it's fine" → an unchecked RP pattern = fail. Explicitly verify or mark N/A.
