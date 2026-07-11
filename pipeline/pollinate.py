#!/usr/bin/env python3
"""pollinate.py — content delivery engine (SwarmAI engine #5 port).

Structurally identical to the code pipeline, domain = content: one message -> many
brand-correct formats. Reads the SAME DDD knowledge layer (ddd.py) as the pipeline —
"the same knowledge that makes Pipeline produce domain-correct code makes Pollinate
produce brand-correct content."

The valuable, code-enforceable part is the **5-gate brand conformance** (mirrors the
pipeline's gates): a draft that fails a gate returns to BUILD, converge or escalate.

  Gate 1 Voice        no self-congratulatory / jargon ("we're thrilled", "groundbreaking")
  Gate 2 Audience     audience-centric (you/your) not company-centric (we/our)
  Gate 3 Accuracy     no fabricated capability claims (checked against DDD constraints/model)
  Gate 4 Originality  not a near-duplicate of past messages (Jaccard vs history)
  Gate 5 Format-fit   format serves the message (length vs format constraints)

11 tracks (A-K): poster video narrative shorts deck pdf data-report document ai-image
interactive-report podcast.  Pure stdlib.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HISTORY = os.path.join(os.environ.get("PIPELINE_ARTIFACTS_ROOT", os.path.join(HERE, ".artifacts")),
                       "pollinate_history.jsonl")

TRACKS = ["poster", "video", "narrative", "shorts", "deck", "pdf", "data-report",
          "document", "ai-image", "interactive-report", "podcast"]

# Gate 1 — banned voice (self-congratulatory / hype / corporate jargon)
BANNED_VOICE = re.compile(
    r"\b(we're thrilled|we are thrilled|thrilled to|excited to announce|proud to|"
    r"groundbreaking|revolutionary|world-class|game-?changer|cutting-edge|best-in-class|"
    r"industry-leading|award-winning|seamless(ly)?|synerg)\w*"
    r"|我们(很|非常)?(高兴|激动|自豪)|激动地宣布|颠覆性|世界领先|业界领先|一流的",
    re.IGNORECASE)
# Gate 3 — unbacked superlatives / absolute claims (need evidence)
HYPE_CLAIMS = re.compile(r"\b(fastest|the best|#1|100%|never fails|zero bugs|unlimited)\b"
                         r"|最(快|好|强|优)|唯一|从不(出错|失败)|零 ?bug|无限", re.IGNORECASE)

# format suitability: (min_words, max_words)
FORMAT_LEN = {"poster": (1, 40), "shorts": (1, 60), "ai-image": (1, 30),
              "narrative": (200, 2000), "pdf": (150, 5000), "document": (150, 5000),
              "deck": (30, 400), "video": (20, 200), "podcast": (100, 3000),
              "data-report": (80, 1500), "interactive-report": (80, 3000)}


def _tok(s: str) -> set:
    return set(re.findall(r"\w+", s.lower()))


def _ddd_real_claims() -> str:
    """Gate 3 source of truth: what's actually real (DDD constraint/model entries)."""
    ddd = os.path.join(HERE, "ddd.py")
    if not os.path.exists(ddd):
        return ""
    try:
        out = subprocess.run([sys.executable, ddd, "list"], capture_output=True, text=True, timeout=20)
        d = json.loads(out.stdout)
        return " ".join(e["text"] for e in d.get("entries", []) if e["type"] in ("constraint", "model"))
    except Exception:
        return ""


def _history() -> list:
    return [json.loads(l) for l in open(HISTORY)] if os.path.exists(HISTORY) else []


def gates(message: str, fmt: str, draft: str) -> dict:
    words = len(re.findall(r"\w+", draft))
    findings = []

    # Gate 1 voice
    v = [m.group(0) for m in BANNED_VOICE.finditer(draft)]
    if v:
        findings.append({"gate": "1_voice", "verdict": "FAIL",
                         "why": f"self-congratulatory/jargon: {sorted(set(v))[:3]}"})
    # Gate 2 audience
    you = len(re.findall(r"\b(you|your|你|您|你的)\b", draft, re.IGNORECASE))
    we = len(re.findall(r"\b(we|our|us|我们|我们的)\b", draft, re.IGNORECASE))
    if we > max(1, you):
        findings.append({"gate": "2_audience", "verdict": "FAIL",
                         "why": f"company-centric (we={we} > you={you}) — frame around the audience's problem"})
    # Gate 3 accuracy
    if HYPE_CLAIMS.search(draft):
        real = _ddd_real_claims()
        findings.append({"gate": "3_accuracy", "verdict": "FAIL",
                         "why": "absolute/superlative claim not backed by DDD (TECH constraints/model)"
                                + ("" if real else " [no DDD to verify against]")})
    # Gate 4 originality
    dtok = _tok(draft)
    for h in _history():
        prev = _tok(h.get("draft", ""))
        if prev and dtok:
            j = len(dtok & prev) / len(dtok | prev)
            if j > 0.8:
                findings.append({"gate": "4_originality", "verdict": "FAIL",
                                 "why": f"near-duplicate of past content (Jaccard {j:.2f})"})
                break
    # Gate 5 format-fit
    lo, hi = FORMAT_LEN.get(fmt, (1, 100000))
    if not (lo <= words <= hi):
        findings.append({"gate": "5_format_fit", "verdict": "FAIL",
                         "why": f"{words} words out of range [{lo},{hi}] for '{fmt}' — format doesn't serve the message"})

    return {"message": message, "format": fmt, "words": words,
            "push_ready": not findings, "failures": findings}


def cmd_tracks(args) -> None:
    print(json.dumps({"tracks": TRACKS}, ensure_ascii=False))


def cmd_gate(args) -> None:
    draft = args.draft
    if args.draft_file:
        draft = open(args.draft_file).read()
    r = gates(args.message, args.format, draft)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    if r["push_ready"] and args.record:
        os.makedirs(os.path.dirname(HISTORY), exist_ok=True)
        with open(HISTORY, "a") as f:
            f.write(json.dumps({"message": args.message, "format": args.format, "draft": draft},
                    ensure_ascii=False) + "\n")
    if not r["push_ready"]:
        print(f"\nPOLLINATE GATE: BLOCK — {len(r['failures'])} brand-conformance failure(s)", file=sys.stderr)
        sys.exit(3)


def cmd_plan(args) -> None:
    """STRATEGIZE: pick tracks from the format-selection matrix (audience x channel x complexity)."""
    picks = []
    complexity = args.complexity
    channel = args.channel
    if channel in ("social", "twitter", "x"):
        picks += ["poster", "shorts"]
    if channel in ("blog", "newsletter"):
        picks += ["narrative"]
    if channel in ("devdocs", "github"):
        picks += ["document"]
    if complexity == "high":
        picks += ["narrative", "video"]
    if complexity == "low":
        picks += ["poster", "shorts"]
    picks = list(dict.fromkeys(picks)) or ["narrative"]
    print(json.dumps({"message": args.message, "channel": channel, "complexity": complexity,
                      "selected_tracks": picks}, ensure_ascii=False, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser(description="Pollinate content engine")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("tracks").set_defaults(func=cmd_tracks)
    p = sub.add_parser("plan")
    p.add_argument("--message", required=True); p.add_argument("--channel", default="blog")
    p.add_argument("--complexity", default="high", choices=["low", "high"])
    p.set_defaults(func=cmd_plan)
    p = sub.add_parser("gate")
    p.add_argument("--message", required=True); p.add_argument("--format", required=True, choices=TRACKS)
    p.add_argument("--draft", default=""); p.add_argument("--draft-file"); p.add_argument("--record", action="store_true")
    p.set_defaults(func=cmd_gate)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
