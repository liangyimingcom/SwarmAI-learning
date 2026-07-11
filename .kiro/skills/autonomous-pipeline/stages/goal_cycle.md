# Stage ⑨ GOAL_CYCLE — Iterative Goal Pursuit (Goal Mode)

> Only in the `goal` profile. Loop BUILD+TEST internally until the Definition of Done is
> met. **MeshClaw:** this maps to the autonudge Goal loop + `cron_add` for overnight
> autonomy (the same mechanism used for LeagueApparel / aichonglang).

## Pre-Cycle Setup
Load evaluation, init a progress file (DoD criteria table + current state), record the
initial commit, set the cycle counter, init velocity metrics.

## Per-Cycle Loop (exit-first design)
1. **Budget Gate** — EXIT if remaining < threshold.
2. **DoD Check** — EXIT if all criteria met (checked FIRST, before doing work).
3. **Stuck Detection** — EXIT if the last 3 cycles made zero progress.
4. Read progress → 5. Pick the next DoD criterion → 6. Execute (BUILD-equivalent,
   1-3 files/cycle) → 7. Test (per-cycle regression) → 8. Update progress →
   9. Mini-Reflect (2-3 sentences) → 9.5 Track velocity.
10. **Periodic REVIEW Gate** — every N cycles, run REVIEW on the accumulated diff.
11. **Revert Check** — EXIT if 2 consecutive cycles ended in revert.
12. Loop.

## DoD criteria
- `command` type (preferred): shell command, exit 0 = pass.
- `rubric` type: explicit pass/fail rubric — only when inherently subjective.
- >50% vague rubrics, or all-rubric with no measurable metric → ESCALATE (too subjective).

## Safeguards
Budget gate · stuck detection · regression revert · max cycles. Regression protocol: max
2 attempts to fix a failing test; 2nd fail → revert the cycle's changes (progress file
preserved).

## MeshClaw wiring
- **Overnight:** `cron_add` fires a cycle every N hours; each run reads the progress file,
  advances one DoD criterion, checks DoD, stops + notifies when met.
- **Stop mechanism:** STOP file + `autonudge_stop` (double stop) — the pattern proven on
  LeagueApparel (7 cycles) and aichonglang.

## Final
DoD met → adversarial review on the TOTAL changeset → advance to DELIVER (Gate 2).

## Output artifact (`publish --stage goal_cycle`)
```json
{
  "cycles": 7,
  "dod_met": true,
  "dod_criteria": [{"type":"command","check":"pytest …","desc":"…","met":true}],
  "velocity": {"per_cycle_deltas":[…],"reverts":0},
  "final_commit": "…"
}
```
