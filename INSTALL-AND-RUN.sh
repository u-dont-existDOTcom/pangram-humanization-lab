#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export LANGGRAPH_STRICT_MSGPACK=true
PYTHON="${PYTHON:-python3}"

if ! "$PYTHON" - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3,10) else 1)
PY
then
  echo "Python 3.10+ is required." >&2
  exit 2
fi

for cmd in git claude codex; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Required command is unavailable: $cmd" >&2
    exit 2
  fi
done

if [ ! -x .venv/bin/python ]; then
  "$PYTHON" -m venv .venv
fi

mkdir -p .state/dependencies
RESOLVED_LOCK=".state/dependencies/requirements.resolved.lock"
RESOLUTION_REPORT=".state/dependencies/pip-resolution.json"
RESOLUTION_META=".state/dependencies/requirements.resolved.json"

if ! .venv/bin/pip install --help 2>/dev/null | grep -q -- '--dry-run'; then
  echo "The bundled install workflow requires a pip version with --dry-run/--report support." >&2
  echo "Use the project target Python 3.12+ so venv provides a recent pip." >&2
  exit 2
fi

if ! PYTHONPATH=src .venv/bin/python scripts/resolve_dependency_lock.py check \
    --source requirements.lock --lock "$RESOLVED_LOCK" --metadata "$RESOLUTION_META"; then
  .venv/bin/pip install --dry-run --ignore-installed --report "$RESOLUTION_REPORT" \
    --requirement requirements.lock
  PYTHONPATH=src .venv/bin/python scripts/resolve_dependency_lock.py build \
    --report "$RESOLUTION_REPORT" --source requirements.lock \
    --out "$RESOLVED_LOCK" --metadata "$RESOLUTION_META"
fi

.venv/bin/pip install --require-hashes --requirement "$RESOLVED_LOCK"
.venv/bin/pip install --no-deps --no-build-isolation -e .

# Autonomous repair requires a clean local Git baseline.  Reconcile the exact
# release overlay before repairable pytest so a verified Codex patch can be
# promoted safely while preserving .state.
.venv/bin/python scripts/reconcile_release_baseline.py --root .

# Preflight failures occur before LangGraph can enter its repair node. Route the
# exact pytest command through the same isolated Codex repair controller instead
# of stopping and asking the owner to relay logs.
.venv/bin/python -m authorial_flow.bootstrap_repair --root . -- .venv/bin/python -m pytest -q

# Live capability smoke belongs to installation, not to ordinary test runs. It spends no Pangram task.
if [ "${AUTHORIAL_SKIP_LIVE_SMOKE:-0}" != "1" ]; then
  SMOKE_ARGS=(--claude --codex --heartbeat)
  if [ -n "${PANGRAM_API_KEY:-}" ]; then
    SMOKE_ARGS+=(--pangram)
  fi
  set +e
  .venv/bin/python -m authorial_flow.bootstrap_repair --root . --phase installer-live-smoke --failure-class PROVIDER_PLUMBING --originating-node provider-smoke --source-provenance INSTALLER_LIVE_SMOKE --evidence-file .state/live-smoke/install-report.json --verify-before-promotion -- .venv/bin/python scripts/live_smoke.py "${SMOKE_ARGS[@]}" --out .state/live-smoke/install-report.json
  SMOKE_RC=$?
  set -e
  if [ "$SMOKE_RC" -eq 3 ]; then
    if [ -t 0 ]; then
      echo "Pangram API key was rejected. Enter a valid key for this run; it will not be saved." >&2
      read -r -s -p "Pangram API key: " PANGRAM_API_KEY
      echo
      if [ -z "${PANGRAM_API_KEY:-}" ]; then
        echo "A valid Pangram API key is required to verify Pangram access." >&2
        exit 3
      fi
      export PANGRAM_API_KEY
      set +e
      .venv/bin/python -m authorial_flow.bootstrap_repair --root . --phase installer-live-smoke --failure-class PROVIDER_PLUMBING --originating-node provider-smoke --source-provenance INSTALLER_LIVE_SMOKE --evidence-file .state/live-smoke/install-report.json --verify-before-promotion -- .venv/bin/python scripts/live_smoke.py "${SMOKE_ARGS[@]}" --out .state/live-smoke/install-report.json
      RETRY_SMOKE_RC=$?
      set -e
      if [ "$RETRY_SMOKE_RC" -eq 3 ]; then
        echo "The replacement Pangram API key was also rejected by the async API." >&2
        exit 3
      elif [ "$RETRY_SMOKE_RC" -eq 4 ]; then
        echo "Pangram authentication succeeded, but the account needs API credits before detector access can be verified." >&2
        exit 4
      elif [ "$RETRY_SMOKE_RC" -ne 0 ]; then
        exit "$RETRY_SMOKE_RC"
      fi
    else
      echo "Pangram credentials need refresh, but no interactive terminal is available." >&2
      exit 3
    fi
  elif [ "$SMOKE_RC" -eq 4 ]; then
    echo "Pangram authentication succeeded, but the account needs API credits before detector access can be verified." >&2
    exit 4
  elif [ "$SMOKE_RC" -ne 0 ]; then
    exit "$SMOKE_RC"
  fi
fi

exec ./RUN.sh "$@"
