---
name: autonomous-pipeline
pipeline_version: "mc-0.1"   # MeshClaw MVP port of SwarmAI Phase 3 (9 stages · 3 gates · 2 modes)
description: >
  Orchestrate the Autonomous Pipeline: one-sentence requirement -> PR-ready delivery.
  DDD drives judgment (steering + memory + lessons), SDD produces the spec, TDD verifies.
  Stages: Evaluate -> Think -> Plan -> Build -> Review -> Test -> Deliver -> Reflect.
  Gates are code-enforced by pipeline_cli.py (structure, not carefulness).
  TRIGGER: "run pipeline", "autonomous pipeline", "pipeline for X", "full pipeline".
  NOT FOR: a single stage — do that stage directly.
tier: lazy
---

# Autonomous Pipeline (MeshClaw port)

> **On activation, read `INSTRUCTIONS.md`** — the mechanical orchestrator (exact commands,
> gate/sub-agent/CodeLens/goal wiring). This file is the map; INSTRUCTIONS.md is the runbook.
>
> The pipeline runs as a skill inside ONE agent session with role-switching.
> The ONLY thing spawned fresh (via `spawn_run`) is the adversarial reviewer at Gate 2
> (and optionally the skeptic at Gate 0/Gate 1) — zero builder bias, sees only the diff.

## The canonical shape — 9 stages · 3 gates · 2 modes

Stages are *what the pipeline does*; gates are the 3 go/no-go checkpoints riding
*inside* the stages; modes are *how execution runs*.

| Gate | Guards | Fires | Enforced by |
|------|--------|-------|-------------|
| **Gate 0** | the *framing* — is the problem understood? | inside EVALUATE | `pipeline_cli.py publish --stage evaluate` (M1 wall + M2 hedge + skeptic verdict) |
| **Gate 1** | the *plan* — right direction, root not symptom? | after PLAN | `publish --stage plan` (skeptic_ssa verdict + structural-vs-patch) |
| **Gate 2** | the *build* — is the code actually correct? | inside DELIVER | `publish --stage deliver` (adversarial_review.profile_tier=="full" + 6-layer) |

**Modes:** `full` = one linear pass + convergence · `goal` = iterate to a measurable DoD
(wire to MeshClaw autonudge + cron for overnight autonomy).

## State machine — every stage goes through the CLI

```bash
PY=python3
CLI=pipeline/pipeline_cli.py

# 1. create the run (profile is IMMUTABLE from here — cannot be downgraded to skip gates)
$PY $CLI run-create --project P --requirement "..." --profile full   # -> run_XXXXXXXX

# 2. for each stage in order: publish its artifact (gate runs here) then advance
$PY $CLI publish --run-id run_XXXXXXXX --stage evaluate --data-file eval.json
$PY $CLI advance --run-id run_XXXXXXXX
# ... think, plan, build, review, test, deliver, reflect ...

# 3. final report
$PY $CLI run-report --run-id run_XXXXXXXX     # -> .artifacts/runs/<id>/REPORT.md
```

`publish` **BLOCKS (exit 3)** if the stage artifact fails its gate. A blocked gate is
not a suggestion — you cannot `advance` past it. That is the whole point: a confident
model cannot rationalize past a gate enforced in code.

## Per-stage contract (what each artifact MUST contain)

See `stages/*.md` for full mechanics. Minimum gate-passing shape:

- **evaluate** — `recommendation` (GO/DEFER/REJECT/ESCALATE), `acceptance_criteria[]`,
  `pre_mortem[]`, and (strict profiles) an `understanding` block
  (`claim` = PRESENT state, no solution language; `evidence` + `evidence_kind`;
  `skeptic_verdict` = SUPPORTED) + an `ambiguity_scan`.
- **think** — `alternatives[]` (>=2), `risk_probe[]` (>=3), `recommendation`.
- **plan** — `file_discovery[]`, `change_spec[]`, and (strict) `skeptic_ssa`
  (`verdict` = SOUND, `structural_vs_patch`).
- **build** — `branch`, `files_changed[]`, `ac_coverage[]` (TDD: red -> green -> verify).
- **review** — `spec_compliance` (fresh sub-agent verdict PASS/WARNING/BLOCK).
- **test** — `passed` (bool), `layers` (ac_driven / dependency_scoped / import_smoke).
- **deliver** — `push_ready` (bool), `adversarial_review` (`profile_tier`, `findings[]`),
  `layers` (L1..L6). Gate 2 requires a fresh `spawn_run` adversarial sub-agent.
- **reflect** — `lessons[]`. Write back to steering / `learn_add` / pipeline_intelligence.json.

## MeshClaw mapping (how the SwarmAI primitives land here)

| SwarmAI | MeshClaw |
|---------|----------|
| DDD docs (PRODUCT/TECH/IMPROVEMENT/PROJECT.md) | `.kiro/steering/*.md` + workspace memory + `learn_add` lessons |
| Code Intelligence (blast radius) | CodeLens MCP (`get_impact`, `find_callers`, `find_affected_tests`, `find_route`) |
| Fresh-context adversarial sub-agent | `spawn_run` (subagent sees only the diff) |
| Goal Mode + Job System (overnight) | autonudge Goal loop + `cron_add` |
| REFLECT write-back | `learn_add` + steering edits + `artifact_update` |
| `pipeline_intelligence.json` | same file, read in EVALUATE / written in REFLECT |

## Verification (before marking complete)

- [ ] REPORT.md generated
- [ ] every stage in the profile sequence has a gate-PASS artifact
- [ ] Gate 2 adversarial evidence present (`profile_tier=="full"` for full/bugfix/goal)
- [ ] decision log entries classified (mechanical / taste / judgment)
- [ ] TDD cycle shown (RED -> GREEN -> no regression)
