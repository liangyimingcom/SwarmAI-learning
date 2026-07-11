#!/usr/bin/env python3
"""goal_runner.py — the deterministic half of Goal Mode (stage ⑨ goal_cycle).

The AGENT does the BUILD step each cycle (creative work); THIS script owns the
mechanical safeguards so they can't be rationalized away:
  * DoD check (exit-first)  — run every command criterion; all exit 0 => DONE
  * Budget / max-cycles gate
  * Stuck detection (N cycles, zero criteria newly met)
Wire to MeshClaw autonudge/cron for overnight autonomy (see goal_cycle.md).

Usage:
  python goal_runner.py init  --goal goal.json          # create progress file
  python goal_runner.py check --goal goal.json           # DoD eval -> verdict
  python goal_runner.py cycle-done --goal goal.json --note "what changed"
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def _progress_path(goal: dict) -> str:
    return goal.get("progress_path", os.path.join(HERE, ".artifacts", "goals",
                                                   goal["id"] + ".json"))


def _load_progress(goal: dict) -> dict:
    p = _progress_path(goal)
    if os.path.exists(p):
        return _load(p)
    return {"goal_id": goal["id"], "cycle": 0, "met": [], "history": [],
            "created_at": _now(), "status": "in_progress"}


def _save_progress(goal: dict, prog: dict) -> None:
    p = _progress_path(goal)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        json.dump(prog, f, indent=2, ensure_ascii=False)


def _eval_criterion(c: dict) -> bool:
    if c.get("type") == "command":
        r = subprocess.run(c["check"], shell=True, cwd=c.get("cwd", HERE),
                           capture_output=True, text=True)
        return r.returncode == 0
    return False  # rubric criteria are judged by the agent, reported via cycle-done


def cmd_init(args) -> None:
    goal = _load(args.goal)
    prog = _load_progress(goal)
    _save_progress(goal, prog)
    print(json.dumps({"initialized": goal["id"], "progress": _progress_path(goal),
                      "dod_criteria": [c["id"] for c in goal["dod_criteria"]]}, ensure_ascii=False))


def cmd_check(args) -> None:
    goal = _load(args.goal)
    prog = _load_progress(goal)
    results = []
    met_ids = []
    for c in goal["dod_criteria"]:
        if c.get("type") == "command":
            ok = _eval_criterion(c)
        else:
            ok = c["id"] in prog.get("met", [])  # rubric: agent-marked
        results.append({"id": c["id"], "desc": c.get("desc", ""), "met": ok})
        if ok:
            met_ids.append(c["id"])

    all_met = len(met_ids) == len(goal["dod_criteria"])
    max_cycles = goal.get("max_cycles", 10)
    # stuck: last `stuck_window` cycles added no newly-met criterion
    window = goal.get("stuck_window", 3)
    recent = prog.get("history", [])[-window:]
    stuck = len(recent) >= window and all(h.get("newly_met", 0) == 0 for h in recent)

    if all_met:
        verdict = "DONE"
    elif prog["cycle"] >= max_cycles:
        verdict = "BUDGET_EXHAUSTED"
    elif stuck:
        verdict = "STUCK"
    else:
        verdict = "CONTINUE"

    unmet = [r["id"] for r in results if not r["met"]]
    print(json.dumps({
        "verdict": verdict, "cycle": prog["cycle"], "max_cycles": max_cycles,
        "met": met_ids, "unmet": unmet, "next_criterion": (unmet[0] if unmet else None),
        "criteria": results,
    }, ensure_ascii=False, indent=2))


def cmd_cycle_done(args) -> None:
    """Agent calls this after doing one build step, to advance the counter + record met set."""
    goal = _load(args.goal)
    prog = _load_progress(goal)
    prev_met = set(prog.get("met", []))
    now_met = [c["id"] for c in goal["dod_criteria"]
               if (c.get("type") == "command" and _eval_criterion(c))
               or (c.get("type") != "command" and c["id"] in prev_met)]
    # allow agent to mark a rubric criterion met via --met
    for m in (args.met or []):
        if m not in now_met:
            now_met.append(m)
    newly = len(set(now_met) - prev_met)
    prog["cycle"] += 1
    prog["met"] = now_met
    prog["history"].append({"cycle": prog["cycle"], "at": _now(),
                            "note": args.note, "newly_met": newly, "met_total": len(now_met)})
    if len(now_met) == len(goal["dod_criteria"]):
        prog["status"] = "dod_met"
    _save_progress(goal, prog)
    print(json.dumps({"cycle": prog["cycle"], "newly_met": newly, "met": now_met,
                      "status": prog["status"]}, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser(description="Goal Mode deterministic driver")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("init", "check"):
        p = sub.add_parser(name)
        p.add_argument("--goal", required=True)
    p = sub.add_parser("cycle-done")
    p.add_argument("--goal", required=True)
    p.add_argument("--note", default="")
    p.add_argument("--met", nargs="*", default=[])
    args = ap.parse_args()
    {"init": cmd_init, "check": cmd_check, "cycle-done": cmd_cycle_done}[args.cmd](args)


if __name__ == "__main__":
    main()
