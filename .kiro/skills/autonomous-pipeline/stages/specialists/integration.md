# Specialist — Integration

> Fresh-context adversarial sub-agent. See only the diff.

**Trigger:** new public functions, new modules, registration/wiring points.

## What to check
- **0-caller detection:** a new public function nobody calls = dead code (or missing wiring).
- Registration gaps: barrel export (RP10), route not registered, handler not attached, DI not bound.
- Call-chain compatibility: caller passes what callee expects (RP14).
- Injected-deps leaves the real adapter uncovered (RP45) — is the REAL wiring tested,
  not just the logic with fakes? grep the real method/field names exist.
- Parallel emitters: is the same data produced at another layer that still misbehaves (RP38)?

## Output (JSON, last line)
```json
{"specialist":"integration","verdict":"CLEAN|ISSUES",
 "findings":[{"severity":"HIGH|MED|LOW","confidence":1-10,"repro":"the unwired path","fix":"..."}]}
```

## Confidence rules
HIGH requires showing the function is unreachable or the wiring is absent (cite the gap).
