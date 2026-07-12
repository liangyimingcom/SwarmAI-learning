#!/usr/bin/env bash
# SwarmAI→MeshClaw Port — one-click installer.
# Installs the autonomous-pipeline skill globally and self-checks all 5 engines.
# Usage:  git clone https://github.com/liangyimingcom/SwarmAI-learning && \
#         cd SwarmAI-learning && bash install/install.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIPE="$REPO_ROOT/pipeline"
SKILL_SRC="$REPO_ROOT/.kiro/skills/autonomous-pipeline"
SKILL_DST="${KIRO_SKILLS_DIR:-$HOME/.kiro/skills}"

echo "════════════════════════════════════════════"
echo "  SwarmAI → MeshClaw Port · installer"
echo "════════════════════════════════════════════"
echo "  repo:   $REPO_ROOT"
echo "  skills: $SKILL_DST"
echo

# 1. prerequisites
command -v python3 >/dev/null 2>&1 || { echo "❌ python3 not found — install Python 3.10+ first."; exit 1; }
PYV=$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])')
echo "✅ python3 $PYV (stdlib-only; no pip install needed)"

# 2. install the skill globally (so any MeshClaw session can 'run pipeline for X')
if [ ! -d "$SKILL_SRC" ]; then echo "❌ skill source missing: $SKILL_SRC"; exit 1; fi
mkdir -p "$SKILL_DST"
rm -rf "$SKILL_DST/autonomous-pipeline"
cp -R "$SKILL_SRC" "$SKILL_DST/autonomous-pipeline"
echo "✅ skill installed → $SKILL_DST/autonomous-pipeline (tier:lazy, trigger: 'run pipeline for X')"

# 3. self-check all engines
echo
echo "──── running self-check ────"
if bash "$REPO_ROOT/install/selfcheck.sh" "$PIPE"; then
  echo
  echo "🎉 install OK. Engines verified."
  echo "   • drive the CLI:   python3 $PIPE/pipeline_cli.py run-list"
  echo "   • or in a MeshClaw session say:  run pipeline for <你的需求>"
  echo "   • quickstart guide:  $REPO_ROOT/install/QUICKSTART.md"
  echo "   • (optional) CodeLens blast-radius needs a token — see QUICKSTART §4"
else
  echo "❌ self-check failed — see output above."; exit 1
fi
