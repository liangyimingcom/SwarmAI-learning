#!/usr/bin/env python3
"""Autonomous Pipeline — state machine + code-enforced gates (MeshClaw port of SwarmAI artifact_cli.py).

Philosophy: gates are STRUCTURAL, not behavioral. A confident model cannot
rationalize past a gate that is enforced in code. This CLI is that enforcement.

Three hard gates (mirroring SwarmAI Phase 3):
  * Gate 0  (understanding)  — enforced at `publish --stage evaluate`
                               M1 wall (claim describes PRESENT, no solution language)
                               M2 hedge-scan (hedge terms block unless evidence is concrete)
  * Gate 1  (skeptic/SSA)    — enforced at `publish --stage plan` (skeptic_verdict required, strict)
  * Gate 2  (adversarial)    — enforced when leaving DELIVER: delivery artifact MUST carry
                               adversarial_review.profile_tier == "full" for full/bugfix/goal
Plus: profile immutability (set at run-create, cannot change) and stage-order enforcement.

Pure stdlib. State stored as JSON under <artifacts_root>/runs/<run_id>/.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import uuid
from datetime import datetime, timezone

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
ARTIFACTS_ROOT = os.environ.get(
    "PIPELINE_ARTIFACTS_ROOT",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".artifacts"),
)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTELLIGENCE_PATH = os.environ.get(
    "PIPELINE_INTELLIGENCE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "pipeline_intelligence.json"),
)
LESSONS_PATH = os.environ.get(
    "PIPELINE_LESSONS",
    os.path.join(_PROJECT_ROOT, ".kiro", "steering", "pipeline-lessons.md"),
)

STRICT_PROFILES = {"full", "bugfix", "goal"}
RELAXED_PROFILES = {"trivial", "docs", "research"}
ALL_PROFILES = STRICT_PROFILES | RELAXED_PROFILES

# Stage sequence per profile (mirrors Autonomous-Pipeline-Design.md §Profile Routing)
STAGE_SEQUENCE = {
    "full":     ["evaluate", "think", "plan", "build", "review", "test", "deliver", "reflect"],
    "bugfix":   ["evaluate", "think", "plan", "build", "review", "test", "deliver", "reflect"],
    "trivial":  ["evaluate", "think", "build", "review", "test", "deliver", "reflect"],
    "research": ["evaluate", "think", "reflect"],
    "docs":     ["evaluate", "think", "plan", "deliver", "reflect"],
    "goal":     ["evaluate", "think", "plan", "goal_cycle", "deliver", "reflect"],
}

# Gate 0 — M1: solution language is FORBIDDEN in an understanding.claim (claim = PRESENT state).
SOLUTION_LANGUAGE = re.compile(
    r"\b(i will|we will|i'll|we'll|the fix is|should add|add a |add an |"
    r"refactor|implement|introduce|rewrite|i plan to|let's|going to|the solution)\b"
    r"|我会|我将|我要|我打算|我准备|打算|准备加|修复方案|应该加|应该改|重构|实现一个|改成|新增|计划",
    re.IGNORECASE,
)

# Gate 0 — M2: hedge terms require concrete observation to survive.
HEDGE_TERMS = re.compile(
    r"\b(probably|should be|i think|likely|maybe|perhaps|seems|might be|appears)\b"
    r"|似乎|可能|大概|应该是|差不多|视情况|好像",
    re.IGNORECASE,
)
CONCRETE_EVIDENCE_KINDS = {"observation", "code-trace", "repro", "characterization", "premortem"}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_dir(run_id: str) -> str:
    return os.path.join(ARTIFACTS_ROOT, "runs", run_id)


def _run_json_path(run_id: str) -> str:
    return os.path.join(_run_dir(run_id), "run.json")


def _load_run(run_id: str) -> dict:
    p = _run_json_path(run_id)
    if not os.path.exists(p):
        _die(f"run not found: {run_id}")
    with open(p) as f:
        return json.load(f)


def _save_run(run: dict) -> None:
    p = _run_json_path(run["run_id"])
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        json.dump(run, f, indent=2, ensure_ascii=False)


def _stage_path(run_id: str, stage: str) -> str:
    return os.path.join(_run_dir(run_id), f"{stage}.json")


def _die(msg: str, code: int = 2) -> None:
    print(f"BLOCK: {msg}", file=sys.stderr)
    sys.exit(code)


def _ok(payload: dict) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _load_data(args) -> dict:
    if getattr(args, "data_file", None):
        with open(args.data_file) as f:
            return json.load(f)
    if getattr(args, "data", None):
        return json.loads(args.data)
    return {}


# --------------------------------------------------------------------------- #
# Gate validators — return list of BLOCK reasons ([] == pass)
# --------------------------------------------------------------------------- #
def gate0_understanding(data: dict, profile: str) -> list[str]:
    """Gate 0 — the framing. Enforced on the evaluate artifact."""
    errs: list[str] = []
    strict = profile in STRICT_PROFILES
    u = data.get("understanding")

    if u is None:
        if strict:
            errs.append("Understanding gate: strict profile requires an `understanding` block.")
        return errs  # relaxed profiles are exempt

    claim = (u.get("claim") or "").strip()
    evidence = (u.get("evidence") or u.get("observation_evidence") or "").strip()
    ekind = (u.get("evidence_kind") or "").strip()
    verdict = (u.get("skeptic_verdict") or "").strip().upper()

    if not claim:
        errs.append("Understanding gate: `claim` is empty.")
    if not evidence:
        errs.append("Understanding gate: `evidence` is empty.")

    # M1 — the wall: claim must describe the PRESENT, not a plan/fix.
    if SOLUTION_LANGUAGE.search(claim):
        errs.append(
            "Understanding gate M1: `claim` contains solution language "
            "(it must describe the PRESENT state, not the fix). Move the fix to THINK."
        )

    # M2 — hedge scan: a hedge blocks unless evidence is concrete + non-hedged.
    if HEDGE_TERMS.search(claim) or HEDGE_TERMS.search(evidence):
        concrete = ekind in CONCRETE_EVIDENCE_KINDS and not HEDGE_TERMS.search(evidence)
        if not concrete:
            errs.append(
                "Understanding gate M2: hedge term present but evidence is not a concrete "
                f"observation (evidence_kind={ekind!r}). Resolve the hedge with an observation."
            )

    # skeptic verdict routing (M3 result recorded by the agent)
    if strict:
        if verdict not in {"SUPPORTED", "UNSUPPORTED", "ALREADY-SATISFIED", "WRONG-FRAME"}:
            errs.append("Understanding gate M3: `skeptic_verdict` missing/invalid for strict profile.")
        elif verdict != "SUPPORTED":
            errs.append(
                f"Understanding gate M3: skeptic_verdict={verdict} — do NOT advance. "
                "Re-frame from observation before THINK."
            )

    # Ambiguity scan (strict only)
    if strict:
        scan = data.get("ambiguity_scan")
        if not isinstance(scan, dict):
            errs.append("Ambiguity scan: strict profile requires an `ambiguity_scan` block.")
        else:
            for h in scan.get("hits", []):
                if len((h.get("resolution") or "")) < 12:
                    errs.append(
                        f"Ambiguity scan: hit {h.get('term')!r} has no real resolution "
                        "(>=12 chars) — an unresolved hit BLOCKS."
                    )
    return errs


def gate_evaluate(data: dict, profile: str) -> list[str]:
    errs = gate0_understanding(data, profile)
    rec = (data.get("recommendation") or "").upper()
    if rec not in {"GO", "DEFER", "REJECT", "ESCALATE"}:
        errs.append("evaluate: `recommendation` must be GO/DEFER/REJECT/ESCALATE.")
    if rec == "GO" and not data.get("acceptance_criteria"):
        errs.append("evaluate: GO requires a non-empty `acceptance_criteria` list.")
    if not data.get("pre_mortem"):
        errs.append("evaluate: `pre_mortem` array is mandatory on GO (Pre-mortem Gate).")
    return errs


def gate_plan(data: dict, profile: str) -> list[str]:
    """Gate 1 — the plan (skeptic + SSA). Enforced on the plan artifact."""
    errs: list[str] = []
    if not data.get("change_spec"):
        errs.append("plan: `change_spec` (ordered atomic sub-changes) is required.")
    if not data.get("file_discovery"):
        errs.append("plan: `file_discovery` is required (search before designing).")
    if profile in STRICT_PROFILES:
        ssa = data.get("skeptic_ssa")
        if not isinstance(ssa, dict):
            errs.append("Gate 1: strict profile requires a `skeptic_ssa` block (skeptic + SSA sub-agent).")
        else:
            verdict = (ssa.get("verdict") or "").strip().upper()
            if verdict not in {"SOUND", "WRONG-DIRECTION", "MISSED-CONSTRAINT", "WRONG-LAYER", "API-HALLUCINATION"}:
                errs.append("Gate 1: `skeptic_ssa.verdict` missing/invalid.")
            elif verdict != "SOUND":
                errs.append(f"Gate 1: skeptic verdict={verdict} — plan not sound, do NOT advance to BUILD.")
            if "structural_vs_patch" not in ssa:
                errs.append("Gate 1: `skeptic_ssa.structural_vs_patch` judgment is required.")
    return errs


def gate_deliver(data: dict, profile: str) -> list[str]:
    """Gate 2 — the build (adversarial). Enforced on the delivery artifact."""
    errs: list[str] = []
    if not isinstance(data.get("push_ready"), bool):
        errs.append("deliver: `push_ready` must be a boolean.")
    adv = data.get("adversarial_review")
    if not isinstance(adv, dict):
        errs.append("Gate 2: `adversarial_review` block is MANDATORY (non-negotiable).")
    else:
        if profile in {"full", "bugfix", "goal"} and adv.get("profile_tier") != "full":
            errs.append(
                "Gate 2: adversarial_review.profile_tier must == 'full' for full/bugfix/goal "
                "(fresh-context sub-agent review is mechanically required)."
            )
        open_findings = [
            f for f in adv.get("findings", [])
            if str(f.get("severity", "")).upper() in {"HIGH", "MED", "MEDIUM"}
            and str(f.get("status", "")).lower() not in {"resolved", "fixed", "false_positive"}
        ]
        if data.get("push_ready") and open_findings:
            errs.append(f"Gate 2: push_ready=true but {len(open_findings)} unresolved HIGH/MED finding(s).")
    # 6-layer gate summary
    layers = data.get("layers", {})
    if data.get("push_ready"):
        for L in ("L1_tests", "L2_types", "L3_no_regression", "L4_adversarial", "L5_ddd", "L6_decisions"):
            if not layers.get(L):
                errs.append(f"deliver 6-layer gate: {L} not marked pass — cannot be push_ready.")
    return errs


# Light presence checks for the remaining stages.
def gate_generic(required: list[str]):
    def _f(data: dict, profile: str) -> list[str]:
        return [f"{k} is required" for k in required if not data.get(k)]
    return _f


STAGE_GATES = {
    "evaluate":   gate_evaluate,
    "think":      gate_generic(["alternatives", "risk_probe", "recommendation"]),
    "plan":       gate_plan,
    "build":      gate_generic(["branch", "files_changed", "ac_coverage"]),
    "review":     gate_generic(["spec_compliance"]),
    "test":       gate_generic(["passed", "layers"]),
    "deliver":    gate_deliver,
    "reflect":    gate_generic(["lessons"]),
    "goal_cycle": gate_generic(["cycles", "dod_met"]),
}


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def cmd_run_create(args) -> None:
    profile = args.profile
    if profile not in ALL_PROFILES:
        _die(f"unknown profile {profile!r}; choose one of {sorted(ALL_PROFILES)}")
    run_id = "run_" + uuid.uuid4().hex[:8]
    intel = _load_intel()
    d = intel["dimensions"]
    intel_snapshot = {
        "runs_total": intel["runs_total"],
        "build_injection_recommendations": d["build_injection_recommendations"],
        "high_risk_shapes": d["abandon_patterns"]["high_risk_shapes"][-5:],
    }
    run = {
        "run_id": run_id,
        "project": args.project,
        "requirement": args.requirement,
        "profile": profile,                       # IMMUTABLE from here on
        "sequence": STAGE_SEQUENCE[profile],
        "status": "in_progress",
        "current_stage": STAGE_SEQUENCE[profile][0],
        "stages_completed": [],
        "created_at": _now(),
        "completed_at": None,
        "gates": {},
        "decision_log": [],
        "intel_at_start": intel_snapshot,         # EVALUATE consumes this automatically
    }
    _save_run(run)
    _ok({"run_id": run_id, "profile": profile, "sequence": run["sequence"],
         "current_stage": run["current_stage"],
         "intel": intel_snapshot,
         "evaluate_must_consider": (
             "Chronic RP patterns to inject into BUILD: "
             + ", ".join(intel_snapshot["build_injection_recommendations"])
             if intel_snapshot["build_injection_recommendations"]
             else "no prior intelligence (first runs)"
         )})


def cmd_publish(args) -> None:
    run = _load_run(args.run_id)
    stage = args.stage
    if stage not in run["sequence"]:
        _die(f"stage {stage!r} is not in the {run['profile']} sequence {run['sequence']}")
    if stage != run["current_stage"]:
        _die(f"out-of-order publish: current stage is {run['current_stage']!r}, got {stage!r}")

    data = _load_data(args)

    # profile immutability guard
    if "profile" in data and data["profile"] != run["profile"]:
        _die(f"profile is immutable: run is {run['profile']!r}, artifact claims {data['profile']!r}")

    errs = STAGE_GATES.get(stage, lambda d, p: [])(data, run["profile"])
    if errs:
        run["gates"][stage] = {"passed": False, "errors": errs, "at": _now()}
        _save_run(run)
        for e in errs:
            print(f"BLOCK: {e}", file=sys.stderr)
        sys.exit(3)

    with open(_stage_path(args.run_id, stage), "w") as f:
        json.dump({"stage": stage, "published_at": _now(), "data": data}, f, indent=2, ensure_ascii=False)
    run["gates"][stage] = {"passed": True, "at": _now()}

    # early-exit routing on evaluate
    if stage == "evaluate":
        rec = (data.get("recommendation") or "").upper()
        if rec in {"DEFER", "REJECT"}:
            run["status"] = rec.lower()
            run["completed_at"] = _now()
        elif rec == "ESCALATE":
            run["status"] = "blocked"
    _save_run(run)
    _ok({"run_id": args.run_id, "stage": stage, "gate": "PASS", "status": run["status"]})


def cmd_advance(args) -> None:
    run = _load_run(args.run_id)
    stage = run["current_stage"]
    gate = run["gates"].get(stage, {})
    if not gate.get("passed"):
        _die(f"cannot advance: stage {stage!r} has not published a gate-passing artifact.")

    seq = run["sequence"]
    idx = seq.index(stage)
    run["stages_completed"].append(stage)
    if idx + 1 >= len(seq):
        run["status"] = "completed"
        run["current_stage"] = None
        run["completed_at"] = _now()
        _save_run(run)
        _ok({"run_id": args.run_id, "status": "completed",
             "stages_completed": run["stages_completed"]})
        return
    run["current_stage"] = seq[idx + 1]
    _save_run(run)
    _ok({"run_id": args.run_id, "advanced_to": run["current_stage"],
         "stages_completed": run["stages_completed"]})


def cmd_run_get(args) -> None:
    _ok(_load_run(args.run_id))


def cmd_run_list(args) -> None:
    """List all runs (id/project/profile/status/current_stage). Optional --status filter."""
    runs_dir = os.path.join(ARTIFACTS_ROOT, "runs")
    rows = []
    if os.path.isdir(runs_dir):
        for rid in sorted(os.listdir(runs_dir)):
            p = os.path.join(runs_dir, rid, "run.json")
            if not os.path.exists(p):
                continue
            # Gate 2 HIGH/MED: one corrupt/half-written/non-dict run.json must NOT
            # take down the whole listing (_save_run is not atomic). Isolate per-run.
            try:
                with open(p) as f:
                    r = json.load(f)
            except (json.JSONDecodeError, OSError, ValueError):
                rows.append({"run_id": rid, "malformed": True})
                continue
            if not isinstance(r, dict):
                rows.append({"run_id": rid, "malformed": True})
                continue
            rows.append({
                "run_id": r.get("run_id", rid),
                "project": r.get("project"),
                "profile": r.get("profile"),
                "status": r.get("status"),
                "current_stage": r.get("current_stage"),
                "stages_completed": len(r.get("stages_completed", [])),
            })
    if args.status:
        rows = [r for r in rows if r.get("status") == args.status]
    _ok({"count": len(rows), "runs": rows})


def cmd_log(args) -> None:
    run = _load_run(args.run_id)
    run["decision_log"].append({
        "at": _now(), "stage": run.get("current_stage"),
        "klass": args.klass, "note": args.note,
    })
    _save_run(run)
    _ok({"logged": True, "count": len(run["decision_log"])})


def cmd_run_report(args) -> None:
    run = _load_run(args.run_id)
    lines = [
        f"# Pipeline Report — {run['run_id']}",
        "",
        f"- **Project:** {run['project']}",
        f"- **Requirement:** {run['requirement']}",
        f"- **Profile:** `{run['profile']}`  ·  **Status:** `{run['status']}`",
        f"- **Created:** {run['created_at']}  ·  **Completed:** {run.get('completed_at')}",
        "",
        "## Stages",
        "",
        "| Stage | Gate | At |",
        "|-------|------|----|",
    ]
    for s in run["sequence"]:
        g = run["gates"].get(s, {})
        mark = "✅ PASS" if g.get("passed") else ("❌ BLOCK" if g else "— pending")
        lines.append(f"| {s} | {mark} | {g.get('at','')} |")
    lines += ["", "## Decision Log", ""]
    if run["decision_log"]:
        for d in run["decision_log"]:
            lines.append(f"- `{d['klass']}` @ {d['stage']}: {d['note']}")
    else:
        lines.append("_(none)_")

    # inline key artifacts
    for s in run["sequence"]:
        p = _stage_path(run["run_id"], s)
        if os.path.exists(p):
            with open(p) as f:
                art = json.load(f)
            lines += ["", f"### Artifact — {s}", "", "```json",
                      json.dumps(art["data"], indent=2, ensure_ascii=False), "```"]
    out = os.path.join(_run_dir(run["run_id"]), "REPORT.md")
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    _ok({"report": out})


# --------------------------------------------------------------------------- #
# Meta-intelligence — the compounding loop (REFLECT write-back)
# --------------------------------------------------------------------------- #
def _load_intel() -> dict:
    if os.path.exists(INTELLIGENCE_PATH):
        with open(INTELLIGENCE_PATH) as f:
            return json.load(f)
    return {
        "version": 1,
        "updated_at": None,
        "runs_total": 0,
        "dimensions": {
            "estimation_accuracy": {"by_profile": {}},           # profile -> {runs, blocked_gates}
            "abandon_patterns": {"high_risk_shapes": []},         # requirement shapes that failed
            "adversarial_value": {"findings_total": 0, "resolved_total": 0},
            "build_injection_recommendations": [],                # chronic RP patterns to inject
        },
    }


def _save_intel(intel: dict) -> None:
    intel["updated_at"] = _now()
    os.makedirs(os.path.dirname(INTELLIGENCE_PATH), exist_ok=True)
    with open(INTELLIGENCE_PATH, "w") as f:
        json.dump(intel, f, indent=2, ensure_ascii=False)


def cmd_run_observe(args) -> None:
    run = _load_run(args.run_id)
    run.setdefault("observations", []).append(
        {"at": _now(), "event": args.event, "stage": run.get("current_stage"), "note": args.note}
    )
    _save_run(run)
    _ok({"observed": args.event, "count": len(run["observations"])})


def _ddd_writeback(run_id: str, lessons: list, rp_new: list) -> list:
    """REFLECT -> DDD: turn lessons into typed ontology entries via ddd.py (subprocess).
    what_worked -> guideline · what_failed -> pitfall · rp_new -> constraint."""
    import subprocess
    ddd = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ddd.py")
    if not os.path.exists(ddd):
        return []
    jobs = []
    for L in lessons:
        if L.get("what_worked"):
            jobs.append(("guideline", L["what_worked"]))
        if L.get("what_failed"):
            jobs.append(("pitfall", L["what_failed"]))
    for r in rp_new:
        jobs.append(("constraint", r))
    added = []
    for t, text in jobs:
        try:
            out = subprocess.run([sys.executable, ddd, "add", "--type", t,
                                  "--text", text, "--source", run_id],
                                 capture_output=True, text=True, timeout=30)
            if out.returncode == 0:
                added.append({"type": t, "id": json.loads(out.stdout).get("added")})
        except Exception:
            pass
    return added


def cmd_run_cultivate(args) -> None:
    """REFLECT write-back: fold this run's lessons into project meta-intelligence +
    append additive lessons to the steering lessons file. This is the compounding loop:
    every run makes the NEXT run's EVALUATE smarter."""
    run = _load_run(args.run_id)
    intel = _load_intel()
    d = intel["dimensions"]

    # 1. outcome + estimation calibration
    intel["runs_total"] += 1
    prof = run["profile"]
    est = d["estimation_accuracy"]["by_profile"].setdefault(prof, {"runs": 0, "blocked_gates": 0})
    est["runs"] += 1
    est["blocked_gates"] += sum(1 for g in run.get("gates", {}).values() if not g.get("passed"))

    outcome = "success" if run["status"] == "completed" else run["status"]

    # 2. read the reflect artifact for lessons / new RP patterns
    lessons, rp_new = [], []
    rp = _stage_path(run["run_id"], "reflect")
    if os.path.exists(rp):
        with open(rp) as f:
            rdata = json.load(f)["data"]
        lessons = rdata.get("lessons", [])
        rp_new = rdata.get("rp_new", [])

    # 3. adversarial value from the delivery artifact
    dp = _stage_path(run["run_id"], "deliver")
    if os.path.exists(dp):
        with open(dp) as f:
            adv = json.load(f)["data"].get("adversarial_review", {})
        found = adv.get("findings", [])
        d["adversarial_value"]["findings_total"] += len(found)
        d["adversarial_value"]["resolved_total"] += sum(
            1 for x in found if str(x.get("status", "")).lower() in {"resolved", "fixed"}
        )

    # 4. chronic RP injection recommendations (dedup)
    inj = d["build_injection_recommendations"]
    for r in rp_new:
        if r not in inj:
            inj.append(r)

    # 5. abandon-pattern learning (only on non-success)
    if outcome not in ("success",):
        shape = {"requirement": run["requirement"][:120], "profile": prof, "outcome": outcome}
        d["abandon_patterns"]["high_risk_shapes"].append(shape)

    _save_intel(intel)

    # 6. append additive lessons to the steering lessons file (Darwinian: dated for decay)
    applied = 0
    learn_candidates = []
    if lessons:
        os.makedirs(os.path.dirname(LESSONS_PATH), exist_ok=True)
        header_needed = not os.path.exists(LESSONS_PATH)
        with open(LESSONS_PATH, "a") as f:
            if header_needed:
                f.write("---\ninclusion: manual\n---\n\n# Pipeline Lessons (auto-cultivated)\n\n"
                        "> Each entry is dated. A lesson unreferenced for 90 days retires (Darwinian decay).\n")
            f.write(f"\n## {run['run_id']} · {run['requirement'][:80]} · {_now()[:10]}\n")
            for L in lessons:
                if "what_worked" in L:
                    f.write(f"- ✅ {L['what_worked']}\n"); applied += 1
                if "what_failed" in L:
                    f.write(f"- ⚠️ {L['what_failed']}\n"); applied += 1
                # reusable pitfalls become learn_add candidates (cross-session behavior change)
                if L.get("reusable") or "what_failed" in L:
                    learn_candidates.append({
                        "rule": L.get("rule") or L.get("what_failed") or L.get("what_worked"),
                        "negative": L.get("negative", ""),
                        "category": L.get("category", "knowledge"),
                        "scope": L.get("scope", "workspace"),
                    })
            for r in rp_new:
                f.write(f"- 🚧 new gate proposed: {r}\n")

    # 6b. emit a learn_add queue for the agent to drain via the MCP tool
    #     (a pure-Python CLI cannot call MCP directly — REFLECT's agent does)
    queue_path = os.path.join(os.path.dirname(ARTIFACTS_ROOT), ".artifacts", "learn_queue.jsonl")
    if learn_candidates:
        os.makedirs(os.path.dirname(queue_path), exist_ok=True)
        with open(queue_path, "a") as f:
            for c in learn_candidates:
                f.write(json.dumps({**c, "run_id": run["run_id"], "at": _now()}, ensure_ascii=False) + "\n")

    # 6c. write lessons back into the DDD knowledge engine as typed ontology entries
    #     (what_worked -> guideline, what_failed -> pitfall, rp_new -> constraint)
    ddd_added = _ddd_writeback(run["run_id"], lessons, rp_new)

    _ok({
        "cultivated": run["run_id"], "outcome": outcome,
        "runs_total": intel["runs_total"],
        "lessons_applied": applied,
        "injection_recommendations": inj,
        "intelligence": INTELLIGENCE_PATH,
        "lessons_file": LESSONS_PATH if lessons else None,
        "learn_add_queue": queue_path if learn_candidates else None,
        "learn_add_directive": (
            "REFLECT agent: call meshclaw learn_add for each queued lesson (category/scope as noted)."
            if learn_candidates else None
        ),
        "learn_candidates": learn_candidates,
        "ddd_added": ddd_added,
    })


def cmd_intel_get(args) -> None:
    """EVALUATE reads this to calibrate profile/budget + inject chronic RP patterns."""
    _ok(_load_intel())


def _learn_queue_path() -> str:
    return os.path.join(os.path.dirname(ARTIFACTS_ROOT), ".artifacts", "learn_queue.jsonl")


def _learn_drained_path() -> str:
    return os.path.join(os.path.dirname(ARTIFACTS_ROOT), ".artifacts", "learn_queue.drained.jsonl")


def _read_jsonl(path: str) -> list:
    if not os.path.exists(path):
        return []
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def cmd_learn_queue(args) -> None:
    """Show pending learn_add candidates (not yet drained). With --drain, mark them
    processed by archiving to learn_queue.drained.jsonl so re-cultivate won't duplicate.
    The AGENT still performs the actual learn_add MCP calls on the pending set."""
    queue = _read_jsonl(_learn_queue_path())
    drained = _read_jsonl(_learn_drained_path())
    drained_keys = {(d.get("rule"), d.get("run_id")) for d in drained}
    pending = [q for q in queue if (q.get("rule"), q.get("run_id")) not in drained_keys]

    if args.drain and pending:
        with open(_learn_drained_path(), "a") as f:
            for p in pending:
                f.write(json.dumps({**p, "drained_at": _now()}, ensure_ascii=False) + "\n")
        _ok({"drained": len(pending), "pending_now": 0,
             "note": "archived to learn_queue.drained.jsonl; agent should have called learn_add for these"})
    else:
        _ok({"pending": pending, "pending_count": len(pending),
             "hint": "agent: call learn_add for each, then `learn-queue --drain` to mark processed"})


# --------------------------------------------------------------------------- #
# Argparse
# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description="Autonomous Pipeline state machine + gates")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("run-create")
    p.add_argument("--project", required=True)
    p.add_argument("--requirement", required=True)
    p.add_argument("--profile", required=True)
    p.set_defaults(func=cmd_run_create)

    p = sub.add_parser("publish")
    p.add_argument("--run-id", required=True)
    p.add_argument("--stage", required=True)
    p.add_argument("--data")
    p.add_argument("--data-file")
    p.set_defaults(func=cmd_publish)

    p = sub.add_parser("advance")
    p.add_argument("--run-id", required=True)
    p.set_defaults(func=cmd_advance)

    p = sub.add_parser("run-get")
    p.add_argument("--run-id", required=True)
    p.set_defaults(func=cmd_run_get)

    p = sub.add_parser("run-list")
    p.add_argument("--status", choices=["in_progress", "completed", "blocked", "reject", "defer"],
                   help="filter by status")
    p.set_defaults(func=cmd_run_list)

    p = sub.add_parser("log")
    p.add_argument("--run-id", required=True)
    p.add_argument("--klass", required=True, choices=["mechanical", "taste", "judgment"])
    p.add_argument("--note", required=True)
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("run-report")
    p.add_argument("--run-id", required=True)
    p.set_defaults(func=cmd_run_report)

    p = sub.add_parser("run-observe")
    p.add_argument("--run-id", required=True)
    p.add_argument("--event", required=True)
    p.add_argument("--note", default="")
    p.set_defaults(func=cmd_run_observe)

    p = sub.add_parser("run-cultivate")
    p.add_argument("--run-id", required=True)
    p.set_defaults(func=cmd_run_cultivate)

    p = sub.add_parser("intel-get")
    p.set_defaults(func=cmd_intel_get)

    p = sub.add_parser("learn-queue")
    p.add_argument("--drain", action="store_true", help="mark pending candidates processed")
    p.set_defaults(func=cmd_learn_queue)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
