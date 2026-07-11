#!/usr/bin/env python3
"""self_evolution.py — self-evolution harness (SwarmAI engine #6 port).

Corrections compound into structure. MINE -> ASSESS -> ACT -> AUDIT, confidence-gated
by DISTINCT-session recurrence (Cepeda: a class repeated across sessions is real; a
burst in one session is not). A recurring correction CLASS climbs a cognitive-patch
ladder until the failure becomes structurally impossible:

  L0 INFORM        1 session     just log it
  L1 LESSON        2 sessions    write a DDD guideline/pitfall (soft memory)
  L2 PROMPT-PATCH  3 sessions    patch the stage instruction (behavioral)
  L3 STRUCTURAL    >=4 sessions  promote to a CODE-ENFORCED gate/RP  <- "carefulness doesn't scale, gates do"

The whole thesis: humans rely on carefulness; the agent relies on structure. When a
class recurs, don't add another lesson — add a gate that makes it impossible.

Store: .artifacts/corrections.jsonl (log) + .artifacts/evolution_state.json (applied level).
Pure stdlib.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.environ.get("PIPELINE_ARTIFACTS_ROOT", os.path.join(HERE, ".artifacts"))
CORR = os.path.join(ART, "corrections.jsonl")
STATE = os.path.join(ART, "evolution_state.json")
GATE_PROP = os.path.join(ART, "structural_gate_proposals.jsonl")

LADDER = [(4, "L3_STRUCTURAL"), (3, "L2_PROMPT_PATCH"), (2, "L1_LESSON"), (1, "L0_INFORM")]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _level(distinct_sessions: int) -> str:
    for threshold, name in LADDER:
        if distinct_sessions >= threshold:
            return name
    return "L0_INFORM"


def _read_corr() -> list:
    if not os.path.exists(CORR):
        return []
    return [json.loads(l) for l in open(CORR) if l.strip()]


def _assess() -> dict:
    """MINE+ASSESS: group corrections by class, count distinct sessions -> level."""
    by_class: dict = {}
    for c in _read_corr():
        d = by_class.setdefault(c["klass"], {"occurrences": 0, "sessions": set(), "texts": []})
        d["occurrences"] += 1
        d["sessions"].add(c.get("session", "default"))
        d["texts"].append(c["text"])
    out = {}
    for k, d in by_class.items():
        ds = len(d["sessions"])
        out[k] = {"occurrences": d["occurrences"], "distinct_sessions": ds,
                  "level": _level(ds), "example": d["texts"][-1]}
    return out


def cmd_record(args) -> None:
    os.makedirs(ART, exist_ok=True)
    with open(CORR, "a") as f:
        f.write(json.dumps({"klass": args.klass, "text": args.text,
                            "session": args.session or "default", "at": _now()},
                           ensure_ascii=False) + "\n")
    a = _assess()[args.klass]
    print(json.dumps({"recorded": args.klass, "distinct_sessions": a["distinct_sessions"],
                      "level_now": a["level"]}, ensure_ascii=False))


def cmd_assess(args) -> None:
    print(json.dumps(_assess(), ensure_ascii=False, indent=2))


def _load_state() -> dict:
    return json.load(open(STATE)) if os.path.exists(STATE) else {}


def cmd_act(args) -> None:
    """ACT: for each class that reached a NEW level since last act, apply the patch."""
    assessed = _assess()
    state = _load_state()
    applied = []
    for k, a in assessed.items():
        prev = state.get(k, "")
        if a["level"] == prev:
            continue                       # no new escalation
        action = {"class": k, "from": prev or "(none)", "to": a["level"]}
        if a["level"] == "L1_LESSON":
            action["patch"] = "DDD guideline/pitfall (soft memory)"
            _ddd_add(k, a["example"])
        elif a["level"] == "L2_PROMPT_PATCH":
            action["patch"] = "patch stage instruction (behavioral) — see stages/*.md"
        elif a["level"] == "L3_STRUCTURAL":
            action["patch"] = "PROMOTE to code-enforced gate/RP (structural)"
            _emit_gate_proposal(k, a)
        else:
            action["patch"] = "log only"
        state[k] = a["level"]
        applied.append(action)
    os.makedirs(ART, exist_ok=True)
    json.dump(state, open(STATE, "w"), ensure_ascii=False, indent=2)
    print(json.dumps({"applied": applied,
                      "structural_gates_file": GATE_PROP if any(x["to"] == "L3_STRUCTURAL" for x in applied) else None},
                     ensure_ascii=False, indent=2))


def _ddd_add(klass: str, text: str) -> None:
    import subprocess
    ddd = os.path.join(HERE, "ddd.py")
    if os.path.exists(ddd):
        try:
            subprocess.run([sys.executable, ddd, "add", "--type", "pitfall",
                            "--text", text, "--source", f"evolution:{klass}"],
                           capture_output=True, timeout=20)
        except Exception:
            pass


def _emit_gate_proposal(klass: str, a: dict) -> None:
    os.makedirs(ART, exist_ok=True)
    with open(GATE_PROP, "a") as f:
        f.write(json.dumps({"class": klass, "level": "L3_STRUCTURAL",
                            "distinct_sessions": a["distinct_sessions"],
                            "proposal": f"Add a code-enforced gate/RP for recurring class '{klass}': {a['example']}",
                            "at": _now()}, ensure_ascii=False) + "\n")


def cmd_audit(args) -> None:
    assessed = _assess()
    ladder = {"L0_INFORM": [], "L1_LESSON": [], "L2_PROMPT_PATCH": [], "L3_STRUCTURAL": []}
    for k, a in assessed.items():
        ladder[a["level"]].append(f"{k} (x{a['distinct_sessions']}sess)")
    print(json.dumps({"ladder": ladder,
                      "structural_gates": len(_read_jsonl(GATE_PROP))}, ensure_ascii=False, indent=2))


def _read_jsonl(p: str) -> list:
    return [json.loads(l) for l in open(p)] if os.path.exists(p) else []


def main() -> None:
    ap = argparse.ArgumentParser(description="Self-evolution: corrections -> structure")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("record"); p.add_argument("--class", dest="klass", required=True)
    p.add_argument("--text", required=True); p.add_argument("--session")
    p.set_defaults(func=cmd_record)
    sub.add_parser("assess").set_defaults(func=cmd_assess)
    sub.add_parser("act").set_defaults(func=cmd_act)
    sub.add_parser("audit").set_defaults(func=cmd_audit)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
