"""wtf_gate.py — TEST-stage changeset risk scorer (Autonomous Pipeline).

Deterministic "should we halt?" gate. Formula (from stages/test.md):
  files_touched(+2 if >3) + unrelated_module(+3) + api_change(+2) + fix_count(+1 if >10)
Score >= HALT_THRESHOLD (5) => L2 BLOCK (something is off; stop and escalate).
"""
from __future__ import annotations

import argparse
import json

__all__ = ["wtf_score", "HALT_THRESHOLD"]

HALT_THRESHOLD = 5


def wtf_score(files_touched: int, touches_unrelated_module: bool,
              api_change: bool, fix_count: int) -> dict:
    """Compute the WTF risk score + verdict.

    >>> wtf_score(2, False, False, 3)["verdict"]
    'PASS'
    >>> wtf_score(5, True, False, 0)["score"]
    5
    >>> wtf_score(5, True, False, 0)["verdict"]
    'HALT'
    >>> wtf_score(1, False, True, 12)
    {'score': 3, 'breakdown': {'files_touched': 0, 'unrelated_module': 0, 'api_change': 2, 'fix_count': 1}, 'verdict': 'PASS'}
    """
    if isinstance(files_touched, bool) or isinstance(fix_count, bool):
        raise TypeError("counts must be int, not bool (bool is an int subclass — Gate 2 F3)")
    if files_touched < 0 or fix_count < 0:
        raise ValueError("counts must be non-negative")
    breakdown = {
        "files_touched": 2 if files_touched > 3 else 0,
        "unrelated_module": 3 if touches_unrelated_module else 0,
        "api_change": 2 if api_change else 0,
        "fix_count": 1 if fix_count > 10 else 0,
    }
    score = sum(breakdown.values())
    return {"score": score, "breakdown": breakdown,
            "verdict": "HALT" if score >= HALT_THRESHOLD else "PASS"}


def main() -> None:
    ap = argparse.ArgumentParser(description="WTF changeset risk gate")
    ap.add_argument("--files", type=int, required=True)
    ap.add_argument("--unrelated", action="store_true")
    ap.add_argument("--api-change", action="store_true")
    ap.add_argument("--fixes", type=int, default=0)
    a = ap.parse_args()
    r = wtf_score(a.files, a.unrelated, a.api_change, a.fixes)
    print(json.dumps(r, ensure_ascii=False))
    # exit 3 for HALT (argparse already uses exit 2 for arg errors — avoid collision; Gate 1 finding)
    raise SystemExit(3 if r["verdict"] == "HALT" else 0)


if __name__ == "__main__":
    main()
