# Runtime Pattern Checklist (RP1–RP50)

Canonical list of recurring production bug patterns that code review + unit tests
consistently miss. REVIEW references this as a **BLOCKING** check — every applicable
pattern must be explicitly verified or marked N/A. **Silence = unchecked = fail.**

Ported from SwarmAI. Example-bug column trimmed for brevity; the trigger + verify
columns are the working checklist. Full examples: SwarmAI `REVIEW_PATTERNS.md`.

| # | Pattern | Trigger | What to verify |
|---|---------|---------|----------------|
| RP1 | subprocess timeout orphan | `Popen`/`create_subprocess_exec` | timeout path calls `proc.kill()` + `await proc.wait()` before re-raise |
| RP2 | subprocess missing binary | spawning a named binary | `FileNotFoundError` caught → friendly "install X" message |
| RP3 | React hook cleanup | new `use*` with refs/subscriptions | `useEffect` return releases streams/timers/listeners |
| RP4 | stale closure | callback reads component state | hold latest via `useRef`, read `.current` |
| RP5 | FormData Content-Type | `FormData` via axios/fetch | NO explicit Content-Type (browser sets boundary) |
| RP6 | setTimeout leak | `setTimeout` in component/hook | id in ref, cleared in cleanup |
| RP7 | error msg / constant mismatch | error text with numbers | message matches the actual constant |
| RP8 | hardcoded env assumption | region/URL/port/path literal | env-configurable with sane default |
| RP9 | API boundary naming | endpoint JSON → frontend | snake_case ↔ camelCase conversion present |
| RP10 | barrel export | new hook/component/service file | exported from `index.ts` |
| RP11 | SDK handler reassignment | `self._handler = new` | old `.close()` before reassign; reset to None after crash |
| RP12 | unstable callback refs | inline arrows as hook props | `useCallback` w/ deps; ref for per-render values |
| RP13 | state machine completeness | enum states + transitions | every state has an enter AND exit path; every transition a trigger |
| RP14 | cross-service param mismatch | A calls B with mapped params | names/semantics match B's contract; no default conflicts |
| RP15 | setTimeout for state propagation | `setTimeout(...,0)` sequencing state | the ref/state read is set BEFORE the timeout, not by concurrent render |
| RP16 | concurrent async without ordering | N async in loop w/ `.then` | sequential `await` or `Promise.all` + indexed insert |
| RP17 | unsanitized string in structured fmt | dynamic text in HTML/JSON/SQL/shell | escape per target (`html.escape`, params, `shlex.quote`) |
| RP18 | timezone date boundary | SQL `date('now')` for "today" | write+query same TZ; desktop uses local time not UTC |
| RP19 | deprecated stdlib API | `get_event_loop`/`utcnow`/`warn` | use 3.12+ replacements |
| RP20 | nested clickable propagation | onClick inside onClick | inner calls `e.stopPropagation()` |
| RP21 | popover toggle + click-outside race | popover + mousedown outside | toggle uses `onMouseDown`+stopPropagation or ref-exclude |
| RP22 | ref/state desync on programmatic input | `setState` value also read via ref | sync ref alongside: `ref.current=v; setState(v)` |
| RP23 | conditional layout empty children | grid/flex w/ conditional children | collapse when one side empty (no blank column) |
| RP24 | cross-language serialization fmt | lang A JSON → lang B parser | match exact byte format (`": "` vs `":"`); test real serializer output |
| RP25 | blast radius — lifecycle not traced | infra/release/deploy/CI/config | trace every build→deploy→run link; check CONSUMERS you didn't modify |
| RP26 | deprecated API vs current docs | framework patterns | verify against CURRENT official docs, not training data |
| RP27 | non-deterministic output ordering | returns list/dict/set for display/compare | explicitly sorted or insertion-ordered or documented-unordered |
| RP28 | schema migration without rollback | `ALTER TABLE`/new column | documented reverse step or additive-only; can prev version deploy? |
| RP29 | YAGNI — unnecessary abstraction | interface/ABC w/ ≤1 impl, new flag w/ 1 value | delete it if removing makes code simpler |
| RP30 | hook no-op path scaling | code in per-session/cron hook | no-op cost O(recent) not O(total history); add mtime/cursor bound |
| RP31 | synthetic-only test data | processes external-source data | ≥1 test uses production-representative data, not dev-crafted |
| RP32 | re-filtering curated input | input from LLM/human/validator + own filter | route (where) don't re-filter (whether); no double-gate signal loss |
| RP33 | multi-shape function return | try/except or flag → different dict shape | ALL consumer tests cover ALL return shapes |
| RP34 | shell var scope across Bash calls | `$VAR` set in a prior tool call | re-derive/read-from-file in each block (each Bash = fresh shell) |
| RP35 | shared executor/pool contention | `to_thread`/`run_in_executor(None)` >1s | dedicated pool if >5s block + latency-sensitive co-consumers |
| RP36 | fix-removes-failure-mode regression | fix makes a previously-failing path succeed | audit new load/resources the now-reachable path consumes |
| RP37 | process tree lifetime mismatch | subprocess spawned from short-lived session | detach (`setsid`/`start_new_session`) or spawn from daemon |
| RP38 | parallel-emitter symptom persistence | data produced/rendered at 2 layers | apply fix to EVERY emitter or a shared upstream point |
| RP39 | detached re-exec silent no-op | `setsid`/`nohup`/`&` re-run of `$0` | absolute path + fixed interpreter + platform support + observable result; test E2E |
| RP40 | single-platform compile misses cross break | new `#[cfg(target_os)]` item | gate all callers OR keep helper un-gated w/ inner cfg; flag CI if no cross-toolchain |
| RP41 | non-orthogonal liveness discriminator | "is X stuck?" acts (kill/restart) on 1 signal | signal reads DIFFERENTLY healthy vs failing; add orthogonal 2nd signal; fail-safe on ambiguous |
| RP42 | sample-encoded discriminator | matcher tuned to observed positives, high act-cost | validate on a NEGATIVE corpus; structural signals over one surface pattern |
| RP43 | destructive op keyed by non-unique field | remove/overwrite selected by title/name | match by STABLE IDENTITY (pk / (title,section)); test same-key collision survives |
| RP44 | identity-gate keyed by raw name | allow/deny on caller string | casefold + `.resolve()`+confine + inode identity; default-deny; test alias corpus |
| RP45 | injected-deps leaves real adapter uncovered | pure logic w/ injected deps + thin wiring | ≥1 test calls the REAL adapter asserting a non-default value; grep real API names exist |
| RP46 | enum-gate misses sibling severity (fail-open) | gate acts on enumerated value set | grep EVERY emitter for full vocabulary; fail-CLOSED on unrecognized non-benign |
| RP47 | test-theater — cannot fail on its bug | new "regression"/"no-mock" test by same agent | not mock-of-subject; mutation-prove RED-on-revert; import prod symbol not re-derive |
| RP48 | stale/false comment (lying comment) | body changed, comment names the mechanism | grep changed tokens vs ±50 comment lines; correct/delete in same diff |
| RP49 | redaction as denylist (fail-open) | strips sensitive fields before a boundary | invert to allowlist-of-KEEP; audit LIST + DETAIL projections both |
| RP50 | verification gate fails OPEN | a pass/block gate (scan/baseline/version) | every "can't inspect" path fails CLOSED; assert positive evidence it ran (files>0, version==pin) |

## Output format (in the review artifact)
```
RP1: pass — proc.kill() in timeout + finally (voice_transcribe.py:92)
RP5: N/A — no FormData in this changeset
RP47: pass — mutation-proven: reverting slug cap line turns test_adv_med_length_cap RED
```

## Maintenance (owned by REFLECT)
Post-pipeline review finds a missed bug → fits an existing RP: tighten its verify criteria;
new pattern: append a row (RP51…) with trigger + verify + the real bug. Update the count in
`stages/review.md`. Without this, lessons live in memory but never reach the checklist.
