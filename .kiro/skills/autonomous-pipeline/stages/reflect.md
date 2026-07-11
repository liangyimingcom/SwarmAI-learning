# Stage ⑧ REFLECT — Extract & Cultivate

> Close the feedback loop. This is the golden "Knowledge compounds every run" arrow.
> Every REFLECT makes the next run's judgment better — or the loop is broken.

## 10-Step Methodology (MeshClaw-adapted)
1. **Extract lessons** — specific, self-contained (not "be more careful").
2. **Write to IMPROVEMENT-equivalent** — What Worked / What Failed. **MeshClaw:** append
   to `.kiro/steering/*.md` and/or `learn_add` (a lesson that changes future behavior in
   an *unrelated* session → `learn_add`; project-local → steering).
3. **Update cross-project memory** — durable facts → workspace memory.
4. **Checklist maintenance** — a bug the reviewers missed but adversarial caught → add a
   new RP pattern so it's caught structurally next time.
5. **ADR gate** — record surprising, costly, or hard-to-reverse decisions.
6. **Dead-code checkpoint** — compare before/after (CodeLens dead-symbol delta).
7. **DDD Cultivation** — auto-apply *additive* lessons to steering; risky changes
   (contradict PRODUCT-equivalent) → proposal queue for the human, never auto-applied.
8. **Structured lessons → run.json** (`log --klass …`).
9. **Record outcome for meta-intelligence** — success/failure + actual effort + lessons
   → `pipeline_intelligence.json` so next EVALUATE calibrates profile/budget and injects
   chronic RP patterns into BUILD.
10. **Regenerate REPORT.md** (`run-report`) with lessons inlined.

## The compounding rule
> Errors are eliminated by **class**, not instance. When a failure recurs, don't add a
> lesson — add a **gate** (a new CLI check / RP pattern) that makes the failure class
> structurally impossible. Human relies on carefulness; the pipeline relies on structure.

## Knowledge must be able to die
Darwinian decay: a lesson unreferenced for 90 days retires. Only-accumulate is how memory
systems rot. Decay is natural selection for what the agent knows.

## Output artifact (`publish --stage reflect`)
```json
{
  "lessons": [
    {"what_worked":"…","class":"pattern"},
    {"what_failed":"…","class":"pitfall"}
  ],
  "ddd_writeback": ["steering/lesson lines to apply"],
  "rp_new": ["RP-mcN: new structural check to add to pipeline_cli.py"],
  "intelligence_update": {"outcome":"success","actual_effort":"…","high_risk_shape":null}
}
```

## Common rationalizations → reality
- "The run succeeded, nothing to reflect" → the compounding loop is the product; a run
  that teaches nothing is a run that didn't compound.
- "I'll just add a lesson" → for a *recurring* class, a lesson is weaker than a gate.
  Prefer the gate.
