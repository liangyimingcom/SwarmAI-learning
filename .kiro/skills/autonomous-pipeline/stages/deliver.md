# Stage ⑦ DELIVER — 6-Layer Convergence + Adversarial

> **Gate 2 (the build) lives here.** Guards the truth of *the code*. Mechanically
> enforced by `publish --stage deliver`: `adversarial_review.profile_tier == "full"` for
> full/bugfix/goal, and `push_ready` requires all 6 layers + zero unresolved HIGH/MED.
> **Cannot be skipped by downgrading the profile** (profile is immutable).

## Quality Convergence Loop (max 3 iterations)
Each iteration checks 6 layers; ALL must pass:

| Layer | Check |
|-------|-------|
| L1 | Tests pass (exit 0) |
| L2 | Type-safe / linter clean |
| L3 | No regressions (pre-existing tests still pass) |
| L4 | Adversarial clean (specialists find no HIGH/MED) |
| L5 | DDD conformance (steering traps + past anti-patterns) |
| L6 | Decisions resolved (every taste/judgment call logged) |

Findings → fix → re-verify → converge. Stuck after 3 iterations → **ESCALATE with a gap
report** (never "ship despite known issues").

## Adversarial Review Gate (BLOCKING, non-negotiable)
`spawn_run` fresh-context specialist sub-agent(s) — **zero build context, sees only the
diff.** Scope-gated specialists (dispatch only those that apply):

| Specialist | Trigger |
|-----------|---------|
| Correctness | always (>50 lines) |
| Security | auth / input / DB / API changes |
| Performance | endpoints, loops, DB queries |
| API Contract | router / endpoint / model changes |
| Concurrency | thread / async / lock code |
| Integration | new public functions (0-caller detection) |
| Operational | daemon / hook / job code |
| State Machine | state enums, lifecycle methods |
| Red Team | >200 lines OR any HIGH found |

Each finding: `severity` (HIGH/MED/LOW) + repro + fix. Record `status` as
resolved/fixed/false_positive once addressed — the CLI counts unresolved HIGH/MED and
blocks `push_ready`.

## Additional Audits
- **Fresh User Audit** — could a new user succeed without editing source?
- **User-Path Latency Trace** — hidden latency / silent failures on real scenarios.
- **Completion Audit** — AC → evidence matrix, independently verified.
- **Push-Ready = BINARY** — PUSH-READY or NOT-PUSH-READY. No "8.5/10". No "close enough".

## Output artifact (`publish --stage deliver`)
```json
{
  "push_ready": true,
  "layers": {"L1_tests":true,"L2_types":true,"L3_no_regression":true,
             "L4_adversarial":true,"L5_ddd":true,"L6_decisions":true},
  "adversarial_review": {
    "profile_tier": "full",
    "subagent": "<spawn id> (fresh context, diff-only)",
    "findings": [{"severity":"MED","repro":"…","status":"resolved","fix":"… + test"}],
    "converged_iterations": 1
  },
  "completion_audit": "N AC + M findings → impl + test, all pass"
}
```

## Common rationalizations → reality
- "Confidence is high, skip adversarial" → self-exemption was corrected 11× (C011-C036);
  the gate is now code-enforced for exactly this reason.
- "It's basically push-ready" → binary. Name the specific gap or it IS push-ready.
- "I'll downgrade to bugfix to move faster" → profile is immutable; that path is closed.
