"""confidence_score.py — deterministic delivery-confidence scorer (1–12).

Folds a pipeline run's gate signals into ONE scalar so DELIVER can report a
breakdown, not just push_ready. Higher = more confident. (Inverse of wtf_gate's
risk score.) Intel injection RP-mc1 (unbounded-string cap) considered: output is a
bounded int/dict, N/A.

Scoring (max 12):
  base                     1
  + gates_passed (cap 6)   up to 6   (evaluate/think/plan/build/review/test/deliver/reflect)
  + adversarial_clean      3         (adversarial_clean AND 0 unresolved HIGH/MED;
                                       caller guarantees profile_tier=="full")
  + all_six_layers         2         (L1..L6 all pass)
Tier: >=10 HIGH · >=6 MED · else LOW.
"""
from __future__ import annotations

import argparse
import json

__all__ = ["confidence_score", "MAX_SCORE"]

MAX_SCORE = 12


def confidence_score(gates_passed: int, adversarial_clean: bool,
                     layers_passed: int, unresolved_high_med: int = 0) -> dict:
    """Return {score(1-12), breakdown, tier}.

    >>> confidence_score(8, True, 6, 0)["score"]
    12
    >>> confidence_score(8, True, 6, 0)["tier"]
    'HIGH'
    >>> confidence_score(3, False, 4, 2)["tier"]
    'LOW'
    >>> confidence_score(0, False, 0, 0)["score"]
    1
    """
    if gates_passed < 0 or layers_passed < 0 or unresolved_high_med < 0:
        raise ValueError("counts must be non-negative")
    # bool guard is symmetric across ALL int params (Gate 2 M2: bool is an int subclass)
    if any(isinstance(x, bool) for x in (gates_passed, layers_passed, unresolved_high_med)):
        raise TypeError("counts must be int, not bool")
    clean = bool(adversarial_clean) and unresolved_high_med == 0
    breakdown = {
        "base": 1,
        "gates_passed": min(gates_passed, 6),
        "adversarial_clean": 3 if clean else 0,
        "all_six_layers": 2 if layers_passed >= 6 else 0,
    }
    # defensive clamp — unreachable given current weights (max 1+6+3+2=12, min 1);
    # guards future weight changes. (Gate 2 L1: documented as defensive, not live.)
    score = max(1, min(sum(breakdown.values()), MAX_SCORE))
    tier = "HIGH" if score >= 10 else "MED" if score >= 6 else "LOW"
    return {"score": score, "breakdown": breakdown, "tier": tier}


def main() -> None:
    ap = argparse.ArgumentParser(description="Delivery confidence scorer (1-12)")
    ap.add_argument("--gates-passed", type=int, required=True)
    ap.add_argument("--adversarial-clean", action="store_true")
    ap.add_argument("--layers-passed", type=int, default=0)
    ap.add_argument("--unresolved", type=int, default=0)
    a = ap.parse_args()
    r = confidence_score(a.gates_passed, a.adversarial_clean, a.layers_passed, a.unresolved)
    print(json.dumps(r, ensure_ascii=False))
    # exit 3 if LOW confidence (distinct from argparse's exit 2)
    raise SystemExit(3 if r["tier"] == "LOW" else 0)


if __name__ == "__main__":
    main()
