#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export LANGGRAPH_STRICT_MSGPACK=true
if [ ! -x .venv/bin/authorial-flow ]; then
  echo "Runtime is not installed. Run ./INSTALL-AND-RUN.sh first." >&2
  exit 2
fi
if [ "$#" -eq 0 ]; then
  if [ -f .state/current-thread.json ]; then
    exec .venv/bin/authorial-flow resume
  fi
  exec .venv/bin/authorial-flow run
fi
case "$1" in
  run|resume|status|answer|package) exec .venv/bin/authorial-flow "$@" ;;
  *) exec .venv/bin/authorial-flow run "$@" ;;
esac
