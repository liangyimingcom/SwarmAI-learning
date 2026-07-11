#!/usr/bin/env python3
"""ddd.py — DDD knowledge engine (SwarmAI engine #3 port).

Self-growing domain knowledge: typed entries (ontology 🏷️) + relations (🕸️) +
Darwinian decay (Ebbinghaus forgetting + Hebbian potentiation) + stage injection.

Ontology — 7 classes (shipped HLD documents 5: guideline/pitfall/decision/model/
process; we add `constraint` [red lines] and `convention` [naming/patterns] as
first-class, which project DDD like surf-forecast clearly needs):

  class        meaning                          home doc        injected during
  ----------   ------------------------------   -------------   ----------------------------
  decision     chose A over B because…          PRODUCT.md      evaluate, plan
  constraint   hard rule / red line (blocking)  TECH.md         evaluate, plan, review, test, deliver
  convention   naming / pattern / how-we-do-it  TECH.md         build, review
  model        what the data/structure is       TECH.md         build
  process      the steps                        TECH.md         build, deliver
  pitfall      don't do this                    IMPROVEMENT.md   build, review, test
  guideline    do this                          IMPROVEMENT.md   build, review

Decay (Darwinian): score = exp(-days_idle / stability); each distinct-session ref
raises stability (Hebbian + Cepeda spacing); floor 0.05; <30d immune; 90d idle
(ref<10) or 180d (ref>=10) => dormant; only `active` entries inject.

Store: ddd/knowledge.jsonl (flat, git-friendly). Pure stdlib.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import uuid
from datetime import datetime, timezone, date

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.environ.get("DDD_STORE", os.path.join(HERE, "ddd", "knowledge.jsonl"))

ONTOLOGY = {
    "decision":   {"doc": "PRODUCT.md",     "inject": ["evaluate", "plan"]},
    "constraint": {"doc": "TECH.md",        "inject": ["evaluate", "plan", "review", "test", "deliver"]},
    "convention": {"doc": "TECH.md",        "inject": ["build", "review"]},
    "model":      {"doc": "TECH.md",        "inject": ["build"]},
    "process":    {"doc": "TECH.md",        "inject": ["build", "deliver"]},
    "pitfall":    {"doc": "IMPROVEMENT.md", "inject": ["build", "review", "test"]},
    "guideline":  {"doc": "IMPROVEMENT.md", "inject": ["build", "review"]},
}
RELATION_TYPES = ["applies_to", "motivated_by", "supersedes", "superseded_by",
                  "extends", "conflicts_with"]
FLOOR = 0.05


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _load() -> list:
    if not os.path.exists(STORE):
        return []
    out = []
    with open(STORE) as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


def _save(entries: list) -> None:
    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    with open(STORE, "w") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def _score(e: dict, today: date) -> float:
    last = date.fromisoformat(e["last"])
    idle = (today - last).days
    return max(FLOOR, math.exp(-idle / max(0.1, e.get("stability", 1.0))))


def _find(entries: list, eid: str) -> dict | None:
    for e in entries:
        if e["id"] == eid or e["id"].startswith(eid):
            return e
    return None


def cmd_add(args) -> None:
    if args.type not in ONTOLOGY:
        raise SystemExit(f"unknown type {args.type}; choose {list(ONTOLOGY)}")
    entries = _load()
    e = {
        "id": "k_" + uuid.uuid4().hex[:8],
        "type": args.type,
        "doc": ONTOLOGY[args.type]["doc"],
        "text": args.text,
        "ref": 0,
        "stability": 30.0,   # days-scale: a fresh entry half-lives over ~weeks, not instantly
        "sessions": [],
        "created": args.created or _today().isoformat(),
        "last": args.last or args.created or _today().isoformat(),
        "decay": "active",
        "maturity": "Sparse",
        "relations": [],
        "source": args.source or "",
    }
    if args.relates_to:
        rel, target = args.relates_to.split(":", 1) if ":" in args.relates_to else ("applies_to", args.relates_to)
        e["relations"].append({"rel": rel, "target": target})
    entries.append(e)
    _save(entries)
    print(json.dumps({"added": e["id"], "type": e["type"], "doc": e["doc"]}, ensure_ascii=False))


def cmd_ref(args) -> None:
    """Hebbian potentiation: a reference from a NEW session raises stability (resists decay)."""
    entries = _load()
    bumped = []
    for eid in args.ids:
        e = _find(entries, eid)
        if not e:
            continue
        e["ref"] += 1
        e["last"] = _today().isoformat()
        if args.session and args.session not in e["sessions"]:
            e["sessions"].append(args.session)          # Cepeda: distinct sessions count
            e["stability"] = round(e["stability"] + 15.0, 3)   # Hebbian (days-scale)
        if e["decay"] == "dormant":
            e["decay"] = "active"                        # revived by use
        bumped.append({"id": e["id"], "ref": e["ref"], "stability": e["stability"]})
    _save(entries)
    print(json.dumps({"bumped": bumped}, ensure_ascii=False))


def cmd_decay(args) -> None:
    """Darwinian pass: recompute scores, transition active->dormant->archived."""
    entries = _load()
    today = _today()
    transitions = []
    for e in entries:
        age = (today - date.fromisoformat(e["created"])).days
        idle = (today - date.fromisoformat(e["last"])).days
        if age < 30:
            continue                                     # grace period for new knowledge
        if e["decay"] == "active":
            if (idle >= 90 and e["ref"] < 10) or (idle >= 180 and e["ref"] >= 10):
                e["decay"] = "dormant"
                transitions.append({"id": e["id"], "to": "dormant", "idle": idle})
        elif e["decay"] == "dormant" and idle >= 180:
            e["decay"] = "archived"
            transitions.append({"id": e["id"], "to": "archived", "idle": idle})
    _save(entries)
    print(json.dumps({"transitions": transitions,
                      "active": sum(1 for e in entries if e["decay"] == "active"),
                      "dormant": sum(1 for e in entries if e["decay"] == "dormant"),
                      "archived": sum(1 for e in entries if e["decay"] == "archived")},
                     ensure_ascii=False))


def cmd_inject(args) -> None:
    """What a pipeline stage should read: ACTIVE entries whose type injects at this stage,
    ranked by Ebbinghaus score (most-alive first)."""
    entries = _load()
    today = _today()
    hits = [e for e in entries if e["decay"] == "active"
            and args.stage in ONTOLOGY[e["type"]]["inject"]]
    hits.sort(key=lambda e: _score(e, today), reverse=True)
    out = [{"id": e["id"], "type": e["type"], "score": round(_score(e, today), 3),
            "text": e["text"]} for e in hits[: args.limit]]
    print(json.dumps({"stage": args.stage, "count": len(out), "inject": out}, ensure_ascii=False, indent=2))


def cmd_list(args) -> None:
    entries = _load()
    today = _today()
    rows = [e for e in entries
            if (not args.type or e["type"] == args.type)
            and (not args.decay or e["decay"] == args.decay)]
    print(json.dumps({"count": len(rows), "entries": [
        {"id": e["id"], "type": e["type"], "decay": e["decay"], "ref": e["ref"],
         "stability": e["stability"], "score": round(_score(e, today), 3),
         "text": e["text"][:60], "relations": e["relations"]} for e in rows]},
        ensure_ascii=False, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser(description="DDD knowledge engine")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add")
    p.add_argument("--type", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--relates-to", help="REL:targetId (e.g. conflicts_with:k_ab12)")
    p.add_argument("--source", default="")
    p.add_argument("--created"); p.add_argument("--last")   # for seeding/demo
    p.set_defaults(func=cmd_add)
    p = sub.add_parser("ref"); p.add_argument("ids", nargs="+"); p.add_argument("--session")
    p.set_defaults(func=cmd_ref)
    p = sub.add_parser("decay"); p.set_defaults(func=cmd_decay)
    p = sub.add_parser("inject"); p.add_argument("--stage", required=True)
    p.add_argument("--limit", type=int, default=20); p.set_defaults(func=cmd_inject)
    p = sub.add_parser("list"); p.add_argument("--type"); p.add_argument("--decay")
    p.set_defaults(func=cmd_list)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
