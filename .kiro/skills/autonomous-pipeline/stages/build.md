# Stage ④ BUILD — TDD Red-Green-Verify

> Implement via **vertical tracer bullets** (RED→GREEN per AC), not horizontal slices.
> Atomic commits, one per change-spec sub-change.

## Purpose
Turn the design_doc into a verified changeset. The unit of progress is a passing AC,
not a written file.

## Mechanics (blocking gates marked ⛔)

1. ⛔ **API Existence Check** — before coding against ANY module: read the target,
   confirm the function/signature exists. **MeshClaw:** `code lookup_symbols` /
   `find_symbol` rather than assuming. Kills API hallucination at the source.

2. ⛔ **Mechanism Declaration** — for system-API usage (locks, signals, atomicity,
   subprocess): declare MECHANISM / ASSUMPTION / VERIFY before using it.

3. **RED → GREEN loop (per AC)** — write the failing test (RED, confirm it fails) →
   implement the minimum code (GREEN) → verify. No implementation before its RED test.

4. **Micro-Replan Trigger** — same AC fails RED→GREEN twice consecutively → STOP, devise
   a different approach (don't grind a third time on the same idea).

5. **Path Symmetry Check** — after each GREEN, enumerate ALL code paths reaching the same
   end state; verify each upholds the postcondition.

6. **VERIFY** — run the changed test files + files importing changed modules (not the
   full suite yet). **MeshClaw:** CodeLens `find_affected_tests` tells you which.

7. **Caller / Interface-Seam Verification** — new public functions must have callers
   (else WARN); cross-module boundaries: methods exist + signatures compatible.

8. **SMOKE** — import/start test; a crash is fixed before advancing.

9. **User-Path Trace** — trace 2-3 real user scenarios through the new code.

10. ⛔ **AC Coverage Matrix (mandatory)** — every PLAN AC has impl + test + verified=true.
    A missing row blocks. Hard cap: max 20 fixes/session → checkpoint.

## Output artifact (`publish --stage build`)
```json
{
  "branch": "pipeline/…",
  "files_changed": ["…"],
  "tdd": {"red":"test failed first","green":"N/N pass","verify":"no regression in scope"},
  "ac_coverage": [{"ac":"AC1","impl":"fn","test":"test_…","verified":true}]
}
```

## Common rationalizations → reality
- "I'll write the test after" → test-after rationalizes whatever the code does; RED first
  proves the test can fail.
- "The API surely takes these args" → surely = hallucination risk. Read it (1 tool call).
- "One more tweak will fix it" (3rd time) → that's the micro-replan trigger; step back.
