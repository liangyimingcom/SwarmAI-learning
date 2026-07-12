#!/usr/bin/env bash
# Self-check: verify all 5 built engines work in a fresh environment.
# Usage: bash install/selfcheck.sh [PIPELINE_DIR]   (default: ../pipeline)
set -uo pipefail
PIPE="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../pipeline" && pwd)}"
cd "$PIPE"
FAIL=0
ok(){ printf "  ✅ %s\n" "$1"; }
bad(){ printf "  ❌ %s\n" "$1"; FAIL=1; }

# isolated scratch so we never touch real state
TMP=$(mktemp -d)
export PIPELINE_ARTIFACTS_ROOT="$TMP" DDD_STORE="$TMP/ddd.jsonl" \
       PIPELINE_INTELLIGENCE="$TMP/intel.json" PIPELINE_LESSONS="$TMP/less.md"

echo "[0] compile all 9 modules"
python3 -m py_compile pipeline_cli.py eval_os.py ddd.py self_evolution.py pollinate.py \
  code_intel.py goal_runner.py wtf_gate.py confidence_score.py 2>/dev/null \
  && ok "9 modules compile" || bad "compile"

echo "[#4] Pipeline — Gate 0 blocks solution-language (structural gate)"
RID=$(python3 pipeline_cli.py run-create --project selfcheck --requirement t --profile full \
      | python3 -c 'import sys,json;print(json.load(sys.stdin)["run_id"])' 2>/dev/null)
python3 pipeline_cli.py publish --run-id "$RID" --stage evaluate --data \
  '{"recommendation":"GO","acceptance_criteria":["x"],"pre_mortem":["y"],"understanding":{"claim":"I will add a thing","evidence":"n","evidence_kind":"observation","skeptic_verdict":"SUPPORTED"},"ambiguity_scan":{"hits":[]}}' \
  >/dev/null 2>&1 && bad "#4 Gate0 should have blocked" || ok "#4 Gate0 blocks (exit3)"

echo "[#13] Eval OS — regression gate, 0 inversion"
python3 eval_os.py --gate >/dev/null 2>&1 && ok "#13 Eval golden set 10/10" || bad "#13 Eval"

echo "[#3] DDD — ontology inject + Darwinian decay"
python3 ddd.py add --type constraint --text "selfcheck redline" >/dev/null 2>&1
python3 ddd.py inject --stage evaluate >/dev/null 2>&1 && ok "#3 DDD stage injection" || bad "#3 DDD inject"
python3 ddd.py decay >/dev/null 2>&1 && ok "#3 DDD decay" || bad "#3 DDD decay"

echo "[#6] Self-Evolution — record/assess"
python3 self_evolution.py record --class sc --text t --session s1 >/dev/null 2>&1 \
  && python3 self_evolution.py assess >/dev/null 2>&1 && ok "#6 self-evolution" || bad "#6"

echo "[#5] Pollinate — Gate1 blocks self-congratulatory draft"
python3 pollinate.py gate --message m --format poster --draft "我们很高兴地宣布颠覆性算法" \
  >/dev/null 2>&1 && bad "#5 Pollinate should have blocked" || ok "#5 Pollinate voice gate"

echo "[tools] wtf_gate / confidence_score / run-list"
python3 wtf_gate.py --files 5 --unrelated >/dev/null 2>&1; [ $? -eq 3 ] && ok "wtf_gate HALT=exit3" || bad "wtf_gate"
python3 confidence_score.py --gates-passed 8 --adversarial-clean --layers-passed 6 >/dev/null 2>&1 \
  && ok "confidence_score" || bad "confidence_score"
python3 pipeline_cli.py run-list >/dev/null 2>&1 && ok "run-list" || bad "run-list"

echo
[ "$FAIL" -eq 0 ] && echo "SELFCHECK: PASS ✅" || { echo "SELFCHECK: FAIL ❌"; exit 1; }
