#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
cd "$ROOT"
. .venv/bin/activate
exec pangram-lab run "${1:-AI.txt}" "${2:-HUMAN.txt}"
