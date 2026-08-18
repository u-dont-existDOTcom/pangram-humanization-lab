#!/usr/bin/env bash

# Terminal-safe owner-machine launcher for the two exact current Romance halves.
# Deliberately avoids persistent strict-mode changes and always returns control.
set +e

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$repo_root" ]; then
  printf '%s\n' "ERROR: run this from inside the pangram-humanization-lab checkout."
  exit 0
fi
cd "$repo_root" || exit 0

log_dir="${HOME}/Téléchargements"
mkdir -p "$log_dir"
log_path="$log_dir/pangram-local-paid-romance.log"
: > "$log_path"

printf '%s\n' "=== Update local runner ===" | tee -a "$log_path"
git pull --ff-only 2>&1 | tee -a "$log_path"
pull_rc=${PIPESTATUS[0]}
printf 'GIT_PULL_EXIT=%s\n\n' "$pull_rc" | tee -a "$log_path"
if [ "$pull_rc" -ne 0 ]; then
  printf '%s\n' "PAID_GATE_RESULT=blocked_git_pull" | tee -a "$log_path"
  exit 0
fi

python_bin="$repo_root/.venv/bin/python"
if [ ! -x "$python_bin" ]; then
  printf '%s\n' "ERROR: repository virtual environment is missing: $python_bin" | tee -a "$log_path"
  printf '%s\n' "PAID_GATE_RESULT=blocked_missing_venv" | tee -a "$log_path"
  exit 0
fi

printf '%s\n' "=== Syntax/import gate ===" | tee -a "$log_path"
"$python_bin" -m py_compile \
  src/pangram_lab/call_budget.py \
  scripts/pangram_local_romance_paid.py 2>&1 | tee -a "$log_path"
compile_rc=${PIPESTATUS[0]}
printf 'COMPILE_EXIT=%s\n\n' "$compile_rc" | tee -a "$log_path"
if [ "$compile_rc" -ne 0 ]; then
  printf '%s\n' "PAID_GATE_RESULT=blocked_compile" | tee -a "$log_path"
  exit 0
fi

printf '%s\n' "=== Read-only paid-run preflight ===" | tee -a "$log_path"
"$python_bin" scripts/pangram_local_romance_paid.py --preflight-only 2>&1 | tee -a "$log_path"
preflight_rc=${PIPESTATUS[0]}
printf 'PREFLIGHT_EXIT=%s\n\n' "$preflight_rc" | tee -a "$log_path"
if [ "$preflight_rc" -ne 0 ]; then
  printf '%s\n' "PAID_GATE_RESULT=blocked_preflight" | tee -a "$log_path"
  exit 0
fi

printf '%s\n' "=== Paid execution ===" | tee -a "$log_path"
printf '%s\n' "Intent: at most one new submission for each exact current Romance half." | tee -a "$log_path"
printf '%s\n' "Budget estimate if both are new: 22 credits total (~USD 1.10 using the repository estimate)." | tee -a "$log_path"
printf '%s\n' "Part 2 will not run if Part 1 becomes ambiguous or otherwise fails." | tee -a "$log_path"

"$python_bin" scripts/pangram_local_romance_paid.py --execute 2>&1 | tee -a "$log_path"
paid_rc=${PIPESTATUS[0]}
printf '\nPAID_RUN_EXIT=%s\nLOG=%s\n' "$paid_rc" "$log_path" | tee -a "$log_path"

if [ "$paid_rc" -eq 0 ]; then
  printf '%s\n' "PAID_GATE_RESULT=completed_or_cached" | tee -a "$log_path"
else
  printf '%s\n' "PAID_GATE_RESULT=stopped_for_evidence_review" | tee -a "$log_path"
fi

# Diagnostic/operator wrapper: preserve terminal even when the paid child stops.
exit 0
