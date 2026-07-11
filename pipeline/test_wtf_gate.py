"""Tests for wtf_gate.wtf_score — each maps to an AC."""
from wtf_gate import wtf_score, HALT_THRESHOLD


# AC1: score is the sum of the 4 weighted components
def test_ac1_breakdown_sum():
    r = wtf_score(4, True, True, 11)
    assert r["breakdown"] == {"files_touched": 2, "unrelated_module": 3, "api_change": 2, "fix_count": 1}
    assert r["score"] == 8


# AC2: verdict HALT iff score >= threshold
def test_ac2_verdict_threshold():
    assert wtf_score(5, True, False, 0)["score"] == HALT_THRESHOLD
    assert wtf_score(5, True, False, 0)["verdict"] == "HALT"
    assert wtf_score(2, False, False, 3)["verdict"] == "PASS"


# AC3: boundary — exactly at threshold halts, just below passes
def test_ac3_boundaries():
    assert wtf_score(4, False, False, 0)["verdict"] == "PASS"   # files>3 => 2, below 5
    assert wtf_score(4, False, True, 11)["verdict"] == "HALT"    # 2+2+1=5
    # fix_count boundary (Gate 1 finding): 10 => no +1, 11 => +1
    assert wtf_score(0, False, False, 10)["breakdown"]["fix_count"] == 0
    assert wtf_score(0, False, False, 11)["breakdown"]["fix_count"] == 1


# Gate 2 F1: threshold off-by-one mutation must go RED — pin files==3 and fix==10 to 0
def test_adv_f1_threshold_edges():
    assert wtf_score(3, False, False, 0)["breakdown"]["files_touched"] == 0  # >3, not >=3
    assert wtf_score(4, False, False, 0)["breakdown"]["files_touched"] == 2
    assert wtf_score(0, False, False, 10)["breakdown"]["fix_count"] == 0     # >10, not >=10


# Gate 2 F4: score exactly 4 (just below threshold) must PASS
def test_adv_f4_score_four_passes():
    r = wtf_score(4, False, True, 0)   # files 2 + api 2 = 4
    assert r["score"] == 4 and r["verdict"] == "PASS"


# Gate 2 F3: bool must raise (bool is an int subclass → silent miscalc)
def test_adv_f3_bool_rejected():
    for bad in [(True, False, False, 0), (1, False, False, True)]:
        raised = False
        try:
            wtf_score(*bad)
        except TypeError:
            raised = True
        assert raised


# Gate 2 F5: CLI exit codes + JSON output have a regression guard
def test_adv_f5_cli_contract():
    import subprocess, sys, os, json as _json
    here = os.path.dirname(os.path.abspath(__file__))
    halt = subprocess.run([sys.executable, "wtf_gate.py", "--files", "5", "--unrelated"],
                          cwd=here, capture_output=True, text=True)
    assert halt.returncode == 3                       # HALT, distinct from argparse's 2
    assert _json.loads(halt.stdout)["verdict"] == "HALT"
    ok = subprocess.run([sys.executable, "wtf_gate.py", "--files", "2"],
                        cwd=here, capture_output=True, text=True)
    assert ok.returncode == 0
    argerr = subprocess.run([sys.executable, "wtf_gate.py"], cwd=here,
                            capture_output=True, text=True)
    assert argerr.returncode == 2                     # argparse usage error stays 2


# pre_mortem: negative counts rejected
def test_premortem_negative_raises():
    for bad in [(-1, False, False, 0), (1, False, False, -5)]:
        raised = False
        try:
            wtf_score(*bad)
        except ValueError:
            raised = True
        assert raised
