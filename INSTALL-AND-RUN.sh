#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
cd "$ROOT"

echo "[setup] Pangram Humanization Lab v2.0.1"
python3 --version

if [[ ! -d .venv ]]; then
  echo "[setup] creating virtualenv"
  python3 -m venv .venv
fi
. .venv/bin/activate
python -m pip install -q --upgrade pip setuptools
python -m pip install -q -e ".[test]"

echo "[verify] deterministic tests"
python -m pytest -q

if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git is required" >&2; exit 2
fi
if ! command -v gh >/dev/null 2>&1; then
  echo "[setup] GitHub CLI missing; attempting apt install"
  sudo apt-get update
  sudo apt-get install -y gh
fi

# Preserve the most useful accumulated research state from the prior working autopilot.
OLD="$HOME/Téléchargements/pangram-codex-autopilot-v1.1"
if [[ -d "$OLD" ]]; then
  mkdir -p legacy
  [[ -f "$OLD/state/WORKING-LESSONS.md" ]] && cp -f "$OLD/state/WORKING-LESSONS.md" legacy/WORKING-LESSONS.md
  [[ -f "$OLD/state/CONTROLLED-TEST-LEDGER.md" ]] && cp -f "$OLD/state/CONTROLLED-TEST-LEDGER.md" legacy/CONTROLLED-TEST-LEDGER.md
  [[ -f "$OLD/PROJECT-CONSTRAINTS.md" ]] && cp -f "$OLD/PROJECT-CONSTRAINTS.md" legacy/PROJECT-CONSTRAINTS.md
  [[ -f "$OLD/AGENTS.md" ]] && cp -f "$OLD/AGENTS.md" legacy/AGENTS.md
  echo "[legacy] copied prior working lessons/control ledger"
fi

# GitHub is established before detector work. gh auth login is invoked interactively if required.
echo "[github] establishing private durable repository before detector work"
pangram-lab github-ensure

echo "[legacy] importing reusable Pangram results (idempotent)"
pangram-lab import-legacy
pangram-lab cache-summary
# Push imported cache/legacy documents before any new paid call.
git add -A
if ! git diff --cached --quiet; then git commit -m "state: import legacy Pangram evidence"; fi
git push -u origin HEAD

AI="${1:-}"
HUMAN="${2:-}"
if [[ -z "$AI" ]]; then
  if [[ -f AI.txt ]]; then AI="$ROOT/AI.txt";
  elif [[ -f "$HOME/Téléchargements/pangram-experiment-harness-v1/AI.txt" ]]; then AI="$HOME/Téléchargements/pangram-experiment-harness-v1/AI.txt"; fi
fi
if [[ -z "$HUMAN" ]]; then
  if [[ -f HUMAN.txt ]]; then HUMAN="$ROOT/HUMAN.txt";
  elif [[ -f "$HOME/Téléchargements/pangram-experiment-harness-v1/HUMAN.txt" ]]; then HUMAN="$HOME/Téléchargements/pangram-experiment-harness-v1/HUMAN.txt"; fi
fi
if [[ ! -f "${AI:-}" || ! -f "${HUMAN:-}" ]]; then
  echo "ERROR: Could not locate AI.txt/HUMAN.txt. Pass exact files: ./INSTALL-AND-RUN.sh AI.txt HUMAN.txt" >&2
  exit 2
fi

echo "[run] AI endpoint: $AI"
echo "[run] Human endpoint: $HUMAN"
echo "[run] Starting adaptive experiment. Completed/cache-hit Pangram calls will NOT be resubmitted."
exec pangram-lab run "$AI" "$HUMAN"
