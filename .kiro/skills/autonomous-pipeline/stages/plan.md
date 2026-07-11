# Stage ③ PLAN — Specify What to Build

> **Gate 1 (the plan) lives at the seam after PLAN.** Guards the truth of *the approach* —
> right direction, root not symptom. Enforced by `publish --stage plan` (skeptic_ssa
> verdict + structural-vs-patch). SDD: exhaustive file discovery BEFORE designing.

## Purpose
Exhaustive file discovery + ordered atomic change spec + test strategy. Skipped by the
`trivial` profile.

## Mechanics

1. **Exhaustive File Discovery (BEFORE designing)** — search → expand → categorize each
   file as MODIFY / TEST / VERIFY / IRRELEVANT. **MeshClaw:** use `grep`/`glob` +
   CodeLens `find_callers` so discovery is grounded, not guessed. Discovery that
   contradicts the THINK approach → return to THINK.

2. **Change Spec** — topologically-sorted atomic sub-changes, each with `id`,
   `depends_on`, the AC it maps to, and a `verify` command. One sub-change = one commit.

3. **Boundaries (three-tier)** — Always / Ask-First / Never, seeded from steering
   conventions + past-failure lessons (`learn_list`).

4. **Success Criteria** — reframed into testable conditions, distinct from the ACs.

5. **Test Strategy Table** — for each AC: how-to-test, mock boundary, input construction.

6. **Impact Projection (blast radius)** — **MeshClaw: CodeLens** `get_impact` +
   `find_affected_tests` on every symbol you'll change. Record downstream callers and the
   test files that must re-run. This IS the "dependents graph" the SwarmAI doc references.

7. **Gate 1 — Skeptic + Same-System-Awareness (SSA), BEHAVIORAL** — `spawn_run` ONE
   fresh-context sub-agent that reviews the PLAN (not the code) and answers:
   - Is the **direction** sound, or is this the wrong layer / a symptom patch?
   - Any **missed constraint** (from steering/TECH-equivalent)?
   - **API hallucination check** — do the functions/signatures the plan calls actually
     exist? (SSA reads the real source.)
   - **Structural vs Patch** judgment — is this a structural fix or a patch that will
     recur? Record the call.
   Verdict ∈ {SOUND, WRONG-DIRECTION, MISSED-CONSTRAINT, WRONG-LAYER, API-HALLUCINATION}.
   Only **SOUND** advances to BUILD (CLI-enforced for strict profiles).

## Blocking Gates
File discovery contradicts approach → back to THINK · missing `change_spec`/
`file_discovery` → CLI rejects · Gate 1 verdict ≠ SOUND → cannot advance.

## Output artifact (`publish --stage plan`)
```json
{
  "approach": "…",
  "file_discovery": [{"path":"…","action":"MODIFY|CREATE|TEST|VERIFY"}],
  "change_spec": [{"id":"c1","desc":"…","depends_on":[],"ac":"AC1","verify":"pytest …"}],
  "boundaries": {"always":[…],"ask_first":[…],"never":[…]},
  "success_criteria": ["…"],
  "test_strategy": [{"ac":"AC1","how":"…","mock":"…","input":"…"}],
  "impact_projection": {"callers":[…],"affected_tests":[…]},
  "skeptic_ssa": {"verdict":"SOUND","structural_vs_patch":"structural: …",
                  "constraints_checked":[…],"api_hallucination_check":"verified: …"}
}
```

## Common rationalizations → reality
- "I'll find the files as I code" → mid-BUILD discovery of a missed file = a re-plan.
  Discovery first is cheaper.
- "The plan is obviously sound, skip the skeptic" → the skeptic catches wrong-layer /
  API-hallucination that a confident builder cannot see in their own plan.
- "This is a quick patch" → patch-vs-structural is a *judgment* to log, not to assume.
