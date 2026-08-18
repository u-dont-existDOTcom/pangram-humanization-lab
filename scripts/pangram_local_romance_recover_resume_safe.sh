#!/usr/bin/env bash

# Recover the already-paid ambiguous Romance Part 1 result without resubmitting
# it, normalize persistent tabs, then resume the paid runner for uncached Part 2.
# This wrapper never leaves strict shell state in the operator's terminal.
set +e

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$repo_root" ]; then
  printf '%s\n' "ERROR: run this from inside the pangram-humanization-lab checkout."
  exit 0
fi
cd "$repo_root" || exit 0

log_dir="${HOME}/Téléchargements"
mkdir -p "$log_dir"
log_path="$log_dir/pangram-local-recover-resume.log"
: > "$log_path"

printf '%s\n' "=== Update local runner ===" | tee -a "$log_path"
git pull --ff-only 2>&1 | tee -a "$log_path"
pull_rc=${PIPESTATUS[0]}
printf 'GIT_PULL_EXIT=%s\n\n' "$pull_rc" | tee -a "$log_path"
if [ "$pull_rc" -ne 0 ]; then
  printf '%s\n' "RECOVER_RESUME_RESULT=blocked_git_pull" | tee -a "$log_path"
  exit 0
fi

python_bin="$repo_root/.venv/bin/python"
if [ ! -x "$python_bin" ]; then
  printf '%s\n' "ERROR: repository virtual environment is missing: $python_bin" | tee -a "$log_path"
  printf '%s\n' "RECOVER_RESUME_RESULT=blocked_missing_venv" | tee -a "$log_path"
  exit 0
fi

printf '%s\n' "=== Local deterministic gate ===" | tee -a "$log_path"
"$python_bin" -m pytest -q 2>&1 | tee -a "$log_path"
test_rc=${PIPESTATUS[0]}
printf '\nLOCAL_TEST_EXIT=%s\n\n' "$test_rc" | tee -a "$log_path"
if [ "$test_rc" -ne 0 ]; then
  printf '%s\n' "RECOVER_RESUME_RESULT=blocked_local_tests" | tee -a "$log_path"
  exit 0
fi

printf '%s\n' "=== Recover already-paid Part 1 without resubmission ===" | tee -a "$log_path"
printf '%s\n' "Part 1 will NOT be submitted again. Restored tabs and bounded History navigation are recovery-only." | tee -a "$log_path"
"$python_bin" scripts/pangram_local_romance_recover_part1.py 2>&1 | tee -a "$log_path"
recover_rc=${PIPESTATUS[0]}
printf '\nRECOVERY_EXIT=%s\n\n' "$recover_rc" | tee -a "$log_path"
if [ "$recover_rc" -ne 0 ]; then
  printf '%s\n' "RECOVER_RESUME_RESULT=stopped_part1_not_recovered" | tee -a "$log_path"
  printf '%s\n' "No repeat detector submission was made." | tee -a "$log_path"
  exit 0
fi

printf '%s\n' "=== Resume exact paid run ===" | tee -a "$log_path"
printf '%s\n' "Part 1 is now a cache hit. Only uncached/unambiguous Part 2 may be submitted." | tee -a "$log_path"
"$python_bin" scripts/pangram_local_romance_paid.py --execute 2>&1 | tee -a "$log_path"
resume_rc=${PIPESTATUS[0]}
printf '\nRESUME_EXIT=%s\nLOG=%s\n' "$resume_rc" "$log_path" | tee -a "$log_path"

if [ "$resume_rc" -eq 0 ]; then
  printf '%s\n' "RECOVER_RESUME_RESULT=complete" | tee -a "$log_path"
else
  printf '%s\n' "RECOVER_RESUME_RESULT=stopped_for_evidence_review" | tee -a "$log_path"
fi

exit 0
