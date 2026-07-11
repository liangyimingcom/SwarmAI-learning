# Stage ① EVALUATE — Should We Build This?

> **Gate 0 (framing) lives here.** Guards the truth of *the problem itself*.
> Enforced by `pipeline_cli.py publish --stage evaluate` (M1 wall + M2 hedge + skeptic verdict + ambiguity scan).

## Purpose
Decide if the task should proceed, select the (immutable) profile, define testable
acceptance criteria. A framing error caught here costs one EVALUATE pass; the same
error caught at Gate 2 has already paid for PLAN + BUILD + REVIEW + TEST.

## Mechanics (in order)

1. **Requirement Clarification (P0)** — parse WHO / WHAT / WHY / WHEN. For each
   undefined element: derivable from DDD (`.kiro/steering/*.md`, memory)? yes → fill +
   note source; no → flag ambiguity. List edge cases (empty, error, concurrent, scale).

2. **Self-Socratic Ambiguity Re-Scan** — re-scan the filled fields + the ACs you're
   about to write for hedge terms (`depends`, `standard`, `typical`, `可能`, `看情况`…).
   For each hit, **self-answer** by reading code / DDD (escalate only genuinely
   unknowable user intent). Record in `ambiguity_scan` — every hit needs a real
   `resolution` (≥12 chars) or it BLOCKS. `hits: []` is valid (proves the scan ran).

3. **Understanding Gate (ALL work types)** — produce a falsifiable `understanding`
   block about the **PRESENT state** (not a plan), backed by an OBSERVATION:
   - **M1 (wall):** `claim` must NOT contain solution language ("I will / the fix is /
     add… / refactor"). CLI blocks it. The fix belongs in THINK.
   - **M2 (observe-not-infer):** a hedge in claim/evidence blocks unless `evidence` is a
     concrete, non-hedged observation (`evidence_kind` ∈ observation/code-trace/repro/
     characterization/premortem).
   - **M3 (skeptic, BEHAVIORAL):** for full/bugfix/goal, `spawn_run` ONE fresh-context
     sub-agent with ZERO of your reasoning: "Is the claim supported by observation or
     only inference? Construct the simplest alternative framing. Is the implied change
     already true (no-op)? Verdict: SUPPORTED / UNSUPPORTED / ALREADY-SATISFIED /
     WRONG-FRAME." Record verdict. Only **SUPPORTED** advances.

   Evidence form varies by `work_type`: bugfix→root cause (repro/ps/log counts);
   existing-feature→real call path (file:line code-trace); refactor→characterization;
   greenfield→problem + who has it; research→the falsifiable question; docs→file refs.

4. **Subsystem Health Audit (P1)** — non-greenfield only: list the subsystem's public
   operations, check 8 operational invariants (OP1-8), add each missing one to the ACs.
   ("fix X" → "fix X + harden the neighborhood.") Skip greenfield / trivial one-liners.

5. **Codebase Complexity Assessment** — **MeshClaw: use CodeLens MCP** instead of a local
   `code_intel.db`. `get_impact` / `find_callers` on the target symbol: >50 callers →
   fragility −0.5; change crosses 3+ modules → coordination −0.5.

6. **Drift Detection (P2, non-blocking)** — code changed since last run but steering/
   DDD didn't? emit `⚠️ Drift` warning. NEVER auto-update design docs from code.

7. **Anti-Repetition Check (BLOCKING)** — scan IMPROVEMENT-equivalent (steering "What
   Failed" + `learn_list` lessons) for structurally similar failed approaches. Match +
   no articulable structural difference → **REJECT**. Record `entries_scanned` even at 0.

8. **Profile Selection** — decision tree (first YES wins): only `.md`→docs; no code
   output→research; ≤1 file, config/const, no logic→trivial; clear bug, known root
   cause→bugfix; **iterative** target (metric/threshold, bulk sweep, N-unknown
   convergence — NOT merely "a test will pass")→goal; else→**full**.
   ⚠️ SIZE/bug gates come BEFORE goal. "A test exits 0" is NOT a goal signal.
   **Profile is immutable after EVALUATE** (CLI-enforced — cannot downgrade to skip gates).

9. **Acceptance Criteria Quality Gate** — every AC = observable OUTCOME, not mechanism.
   3 filters: no-op test (would a value-less no-op still pass? → too weak), user-value
   test, garbage-in test (can it pass with trivially wrong content?). ≥1 AC must be a
   "user would notice" criterion.

10. **Pre-mortem Gate (mandatory on GO)** — "what would make this fail?" → `pre_mortem[]`.

## Blocking Gates
Anti-repetition match → REJECT/ESCALATE · ≥2 unresolvable ambiguities → ESCALATE ·
constraint conflict → ESCALATE · M1/M2/skeptic-verdict/ambiguity → CLI BLOCK.

## Output artifact (`publish --stage evaluate`)
```json
{
  "recommendation": "GO|DEFER|REJECT|ESCALATE",
  "scope": "standard|complex|trivial|bugfix|goal",
  "acceptance_criteria": ["observable + quality-qualified …"],
  "pre_mortem": ["…"],
  "understanding": {"work_type":"…","claim":"PRESENT state","evidence":"observation",
                    "evidence_kind":"code-trace","skeptic_verdict":"SUPPORTED",
                    "alternative_considered":"…"},
  "ambiguity_scan": {"hits":[{"term":"…","resolution":"self-answer: … (≥12 chars)"}],
                     "all_resolved": true}
}
```
GREENFIELD + strict also requires a `working_backwards` block (target_customer,
current_workaround, why_better, must_be_true).

## Exit routing
GO → advance to think · DEFER/REJECT → pipeline ends · ESCALATE → L2 BLOCK (human).

## Common rationalizations → reality
- "Obviously a GO, skip scoring" → obvious tasks have conflicted with non-goals & dup'd
  failed work. Full scoring = 30s.
- "Scope is trivial, I know this" → wrong scope = wrong downstream gates. A 3-file change
  called trivial skipped adversarial review → shipped broken.
- "Requirement's clear, skip clarification" → vague GO → under-specified ACs → builds the
  wrong thing that passes.
