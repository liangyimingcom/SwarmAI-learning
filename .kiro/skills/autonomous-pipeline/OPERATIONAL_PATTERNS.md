# Operational Pattern Checklist (OP1–OP8)

System-level architectural invariants — apply regardless of what code you write.
REVIEW checks these alongside RP1–RP50 for any changeset that adds/modifies a
subsystem's lifecycle operations. EVALUATE's Subsystem Health Audit (P1) also walks
these against every public operation of a touched subsystem.

| # | Pattern | Trigger | What to verify |
|---|---------|---------|----------------|
| OP1 | **Concurrency guard** | state-changing endpoint / bg task | atomic status gate (`UPDATE WHERE status=X` → rowcount 0 on concurrent) or explicit lock |
| OP2 | **Rollback path** | destructive op (deploy/update/migrate/config) | backup BEFORE + restore on failure |
| OP3 | **Data backup** | persistent user data dir (DB/workspace/config) | automated schedule + retention + tested restore |
| OP4 | **Access control on secrets** | endpoint returns creds/tokens/keys | auth guard appropriate to context; never on unauth/over-privileged path |
| OP5 | **Health unauthenticated** | `/health` `/status` monitoring endpoint | reachable WITHOUT creds; returns no secrets |
| OP6 | **Fail-loud placeholders** | template/config/env placeholder value | placeholder MUST fail at runtime if unreplaced (`INVALID_…`, never valid-looking) |
| OP7 | **Single canonical path** | op with >1 way to do it | exactly one canonical path; alternatives deleted or `exit 1`+warn |
| OP8 | **Config consistency** | config in >1 location | all copies in sync OR explicitly `--exclude`d; document source of truth |

## When to apply
**Scoped trigger:** infra / cloud / deploy subsystems only — NOT every endpoint.
Test: "does this manage external resources (EC2/S3/CloudFront/systemd/cron) or credentials?"
- **Check** — lifecycle ops on daemon/CI/release/backup/cron; config templates; placeholders.
- **Skip** — regular API (chat/settings), UI, test-only, in-memory state.

## Output format (in the review artifact)
```
OP1: pass — update() uses atomic status gate (UPDATE WHERE status='running')
OP3: N/A — no persistent data in this changeset
OP4: pass — credentials endpoint has _require_desktop()
```

## Maintenance (owned by REFLECT)
Post-pipeline audit finds an operational gap the checklist missed → append a new OP with
trigger + verify + real example.
