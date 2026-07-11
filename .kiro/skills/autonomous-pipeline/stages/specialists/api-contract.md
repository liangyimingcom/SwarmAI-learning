# Specialist — API Contract

> Fresh-context adversarial sub-agent. See only the diff.

**Trigger:** router / endpoint / model / public-function signature changes.

## What to check
- Breaking changes: removed/renamed field, changed type, new REQUIRED param without default.
- Request/response schema drift vs consumers (RP9 naming, RP24 cross-language format).
- Versioning: does a breaking change bump a version / keep back-compat?
- Every consumer of the changed contract traced and still compatible.
- Enum/status value added but a downstream gate only matches the old set (RP46, fail-open).

## Output (JSON, last line)
```json
{"specialist":"api-contract","verdict":"CLEAN|ISSUES",
 "findings":[{"severity":"HIGH|MED|LOW","confidence":1-10,"repro":"caller that breaks","fix":"..."}]}
```

## Confidence rules
HIGH requires naming the specific consumer that breaks and how.
