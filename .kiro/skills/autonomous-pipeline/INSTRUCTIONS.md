# INSTRUCTIONS — Autonomous Pipeline Orchestrator

> Read this on skill activation. This is the mechanical runbook: exact commands, routing,
> and the sub-agent / CodeLens / goal wiring. Stage *mechanics* live in `stages/*.md`;
> this file is *how to drive them*.

`PIPE=python3 pipeline/pipeline_cli.py` · `CI=python3 pipeline/code_intel.py` ·
`GOAL=python3 pipeline/goal_runner.py`

## 0. On activation
1. Confirm the requirement is one sentence. If vague, that's EVALUATE's job (don't pre-clarify).
2. `RUN=$($PIPE run-create --project P --requirement "…" --profile <profile>)` →
   **the output's `intel` block is read automatically** — note any
   `build_injection_recommendations` (chronic RP patterns) to inject at BUILD.
3. Profile is IMMUTABLE. Pick it via the EVALUATE decision tree (see `stages/evaluate.md`).

## 1. Per-stage loop (drive in sequence)
For each stage in the profile's sequence: do the stage's work → `$PIPE publish --stage S
--data-file s.json` → if it PASSES → `$PIPE advance`. A BLOCK (exit 3) prints the reason;
fix the artifact and re-publish. **You cannot advance past a blocked gate.**

Read the matching `stages/<S>.md` for that stage's mechanics + required artifact fields.

## 2. The three gates — where sub-agents spawn (`spawn_run`, fresh context)
- **Gate 0** (inside EVALUATE, strict profiles): after scoring GO, `spawn_run` ONE skeptic
  with ZERO of your reasoning → refute the `understanding.claim`. Record `skeptic_verdict`.
  Only SUPPORTED advances. (CLI enforces M1 wall + M2 hedge on publish.)
- **Gate 1** (after PLAN, strict): `spawn_run` a Skeptic+SSA sub-agent to review the PLAN
  (not code) — direction / missed constraint / wrong layer / API hallucination / structural
  vs patch. Record `skeptic_ssa.verdict`; only SOUND advances.
- **Gate 2** (inside DELIVER, mandatory for full/bugfix/goal): `spawn_run` the scope-gated
  specialists from `stages/specialists/*.md` (correctness always; others by trigger; red-team
  if >200 lines or any HIGH). They see ONLY the diff. Collect findings → fix → re-verify →
  converge (max 3 iter). Mark each finding `status: resolved`. CLI blocks `push_ready` on any
  unresolved HIGH/MED and requires `adversarial_review.profile_tier=="full"`.

## 3. Code Intelligence (CodeLens) — PLAN & EVALUATE
When the target is an indexed package, ground blast radius in real data, not guesses:
- `$CI symbol --package owner/repo --query NAME` — find the symbol.
- `$CI impact --package owner/repo --symbol NAME` — upstream/downstream blast radius → PLAN `impact_projection`.
- `$CI affected-tests --package owner/repo --symbol NAME` — which tests TEST must re-run.
Skip when the project isn't indexed (fall back to grep/glob).

## 4. Review / Test / Deliver checklists
- REVIEW: run the Litmus pre-gate, then spawn the Spec-Compliance sub-agent; fan out to 3
  parallel sub-agents if >3 files / >100 lines / auth-data-infra. Verify every applicable
  RP1–RP50 (`REVIEW_PATTERNS.md`) + OP1–OP8 (`OPERATIONAL_PATTERNS.md`) explicitly or N/A.
- TEST: 3 layers (AC-driven / dependency-scoped / import-smoke) + WTF gate.
- DELIVER: 6-layer convergence + Gate 2. Push-Ready is BINARY.

## 5. Goal Mode (profile == goal)
Instead of a single BUILD pass, drive `stages/goal_cycle.md` via `goal_runner.py`:
1. `$GOAL init --goal pipeline/goals/<g>.json`
2. Each cycle: `$GOAL check --goal …` → if `DONE`/`BUDGET_EXHAUSTED`/`STUCK` → stop (gap
   report if not DONE). Else do ONE build step for `next_criterion`, run its verify, then
   `$GOAL cycle-done --goal … --note "…"`.
3. Overnight: register a cron (see the paused `goal-loop-*` job) — one cycle per tick.
4. DoD met → Gate-2 adversarial on the total changeset → publish `goal_cycle` → DELIVER.

## 6. REFLECT — close the compounding loop (never skip)
1. `$PIPE publish --stage reflect --data '{"lessons":[…],"rp_new":[…]}'` → `$PIPE advance`.
2. `$PIPE run-cultivate --run-id $RUN` — folds outcome into `pipeline_intelligence.json`,
   appends dated lessons to `.kiro/steering/pipeline-lessons.md`, and emits a
   `learn_add_queue`.
3. **Drain the queue:** for each line in `pipeline/.artifacts/learn_queue.jsonl`, call the
   MeshClaw `learn_add` MCP tool (category/scope as noted). The CLI cannot call MCP — you do.
   Then `$PIPE learn-queue --drain` to mark them processed (so a re-cultivate won't
   re-emit duplicates). `$PIPE learn-queue` shows only not-yet-drained candidates.
4. `$PIPE run-report --run-id $RUN` → `.artifacts/runs/$RUN/REPORT.md`.

## 7. Escalation
Never "ship despite known issues." Stuck after max iterations / budget / L2 BLOCK →
checkpoint + escalate with a gap report. In MeshClaw: notify via `send_message` or a Radar/
HEARTBEAT todo, then stop.
