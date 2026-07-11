# Stage ⑥ TEST — Three-Layer Verification

> Verify correctness at three scopes. Not "run the tests" — run the *right* three layers
> and prove each ran.

## Layers
1. **AC-Driven Verification** — run the tests explicitly declared in `ac_coverage`.
2. **Dependency-Scoped Regression** — run tests importing the changed modules.
   **MeshClaw:** CodeLens `find_affected_tests` enumerates them; else `grep` for imports.
3. **Import Smoke** — for each new module: import without crash.

## Additional Checks
- **WTF Gate (risk score)** — `files_touched(+2 if >3) + unrelated_module(+3) +
  API_change(+2) + fix_count(+1 if >10)`. Score ≥5 → L2 BLOCK (something is off, stop).
- ⛔ **Single-Platform Compile Trap** — a cross-platform changeset cannot report
  fully-green from a single OS. Say so honestly.
- **Max 20 fixes/session** — hard cap; checkpoint after.
- **Exit Evidence Checklist** — confirm all 3 layers actually executed (not skipped).

## Output artifact (`publish --stage test`)
```json
{
  "passed": true,
  "layers": {
    "ac_driven": "N/N declared tests pass",
    "dependency_scoped": "importers of changed modules pass (or none)",
    "import_smoke": "each new module imports clean"
  },
  "regressions": 0,
  "wtf_score": 2
}
```

## Common rationalizations → reality
- "The full suite is green, done" → green ≠ the 3 layers ran. A cross-platform change
  green on one OS is not green.
- "Only 1 test failed, unrelated" → dependency-scoped layer exists precisely to catch the
  "unrelated" regression that isn't.
