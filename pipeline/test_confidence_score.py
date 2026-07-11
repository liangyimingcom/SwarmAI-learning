"""Tests for confidence_score — each maps to an AC. Boundary + mutation-aware (RP47)."""
from confidence_score import confidence_score, MAX_SCORE


# AC1: full green run scores the max and is HIGH
def test_ac1_full_green_max():
    r = confidence_score(8, True, 6, 0)
    assert r["score"] == MAX_SCORE and r["tier"] == "HIGH"
    assert r["breakdown"] == {"base": 1, "gates_passed": 6, "adversarial_clean": 3, "all_six_layers": 2}


# AC2: unresolved HIGH/MED voids the adversarial_clean bonus
def test_ac2_unresolved_voids_clean():
    clean = confidence_score(6, True, 6, 0)["breakdown"]["adversarial_clean"]
    dirty = confidence_score(6, True, 6, 1)["breakdown"]["adversarial_clean"]
    assert clean == 3 and dirty == 0


# AC3: tier thresholds (boundary-pinned so off-by-one mutations go RED)
def test_ac3_tier_boundaries():
    assert confidence_score(6, False, 0, 0)["score"] == 7 and confidence_score(6, False, 0, 0)["tier"] == "MED"
    assert confidence_score(9, True, 0, 0)["tier"] == "HIGH"   # 1+6+3=10
    assert confidence_score(2, False, 4, 0)["tier"] == "LOW"   # 1+2=3 (<6, layers<6)
    # exact tier edges: 6->MED, 5->LOW ; 10->HIGH, 9->MED
    assert confidence_score(5, False, 0, 0)["score"] == 6 and confidence_score(5, False, 0, 0)["tier"] == "MED"
    assert confidence_score(4, False, 0, 0)["score"] == 5 and confidence_score(4, False, 0, 0)["tier"] == "LOW"
    # Gate 2 M1: pin the HIGH lower side (score 9 must be MED) so >=10 -> >=9 mutation goes RED
    assert confidence_score(6, False, 6, 0)["score"] == 9 and confidence_score(6, False, 6, 0)["tier"] == "MED"


# AC4: caps & floor are reachable and pinned (Gate 2 L1: honest name — clamp is defensive/dead)
def test_ac4_caps_and_floor():
    assert confidence_score(100, True, 6, 0)["score"] == 12       # gates cap (6) => max 12
    assert confidence_score(100, True, 6, 0)["breakdown"]["gates_passed"] == 6
    assert confidence_score(0, False, 0, 0)["score"] == 1         # base floor


# pre_mortem: negatives raise, bool rejected on ALL int params (Gate 2 F3/M2 class)
def test_premortem_guards():
    for bad in [(-1, False, 0, 0), (0, False, -1, 0)]:
        try:
            confidence_score(*bad); assert False
        except ValueError:
            pass
    # bool must raise on every int param, including unresolved_high_med (Gate 2 M2)
    for bad in [(True, False, 0, 0), (0, False, 0, True), (0, False, True, 0)]:
        try:
            confidence_score(*bad); assert False
        except TypeError:
            pass


# CLI contract: LOW -> exit 3, else 0, argparse error -> 2
def test_cli_contract():
    import subprocess, sys, os, json as _json
    here = os.path.dirname(os.path.abspath(__file__))
    low = subprocess.run([sys.executable, "confidence_score.py", "--gates-passed", "2"],
                         cwd=here, capture_output=True, text=True)
    assert low.returncode == 3 and _json.loads(low.stdout)["tier"] == "LOW"
    hi = subprocess.run([sys.executable, "confidence_score.py", "--gates-passed", "8",
                         "--adversarial-clean", "--layers-passed", "6"],
                        cwd=here, capture_output=True, text=True)
    assert hi.returncode == 0 and _json.loads(hi.stdout)["tier"] == "HIGH"
    err = subprocess.run([sys.executable, "confidence_score.py"], cwd=here,
                         capture_output=True, text=True)
    assert err.returncode == 2
