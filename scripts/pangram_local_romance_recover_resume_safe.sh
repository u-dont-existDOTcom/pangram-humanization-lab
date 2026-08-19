#!/usr/bin/env bash

# Recover the already-paid ambiguous Romance Part 1 result without resubmitting
# it, normalize persistent tabs, then resume the paid runner for uncached Part 2.
# Recovery uses only the dedicated automation profile and Pangram's read-only
# All Checks/History/result surfaces. It never inspects Joel's ordinary Brave
# profile and never clicks a detector action for Part 1.
# This wrapper never leaves strict shell state in the operator's terminal.
set +e

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$repo_root" ]; then
  printf '%s\n' "ERROR: run this from inside the pangram-humanization-lab checkout."
  exit 0
fi
cd "$repo_root" || exit 0

self_path="$repo_root/scripts/pangram_local_romance_recover_resume_safe.sh"
log_dir="${HOME}/Téléchargements"
mkdir -p "$log_dir"
log_path="$log_dir/pangram-local-recover-resume.log"
diagnostic_path="$log_dir/pangram-local-history-structure-diagnostic.json"

# A running shell does not reload its source file after `git pull`. Preserve the
# first process's log, but when the pull changes this wrapper, exec the new file
# exactly once so the rest of the run uses the newly fetched control flow.
if [ "${PANGRAM_RECOVER_WRAPPER_REEXEC:-0}" = "1" ]; then
  touch "$log_path"
else
  : > "$log_path"
fi
self_hash_before="$(git hash-object "$self_path" 2>/dev/null)"

printf '%s\n' "=== Update local runner ===" | tee -a "$log_path"
git pull --ff-only 2>&1 | tee -a "$log_path"
pull_rc=${PIPESTATUS[0]}
printf 'GIT_PULL_EXIT=%s\n\n' "$pull_rc" | tee -a "$log_path"
if [ "$pull_rc" -ne 0 ]; then
  printf '%s\n' "RECOVER_RESUME_RESULT=blocked_git_pull" | tee -a "$log_path"
  exit 0
fi

self_hash_after="$(git hash-object "$self_path" 2>/dev/null)"
if [ "${PANGRAM_RECOVER_WRAPPER_REEXEC:-0}" != "1" ] \
   && [ -n "$self_hash_before" ] \
   && [ -n "$self_hash_after" ] \
   && [ "$self_hash_before" != "$self_hash_after" ]; then
  printf '%s\n' "WRAPPER_UPDATED=yes; restarting into fetched wrapper before continuing." | tee -a "$log_path"
  PANGRAM_RECOVER_WRAPPER_REEXEC=1 exec bash "$self_path"
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

# Remove only the previous privacy-bounded diagnostic so a failed new attempt
# cannot accidentally append stale structure from an earlier UI version.
rm -f -- "$diagnostic_path"

printf '%s\n' "=== Recover already-paid Part 1 without resubmission ===" | tee -a "$log_path"
printf '%s\n' "Part 1 will NOT be submitted again. Pangram All Checks/History navigation is recovery-only." | tee -a "$log_path"
"$python_bin" scripts/pangram_local_romance_recover_part1_history.py 2>&1 | tee -a "$log_path"
recover_rc=${PIPESTATUS[0]}
printf '\nRECOVERY_EXIT=%s\n\n' "$recover_rc" | tee -a "$log_path"
if [ "$recover_rc" -ne 0 ]; then
  if [ -f "$diagnostic_path" ]; then
    printf '%s\n' "=== Safe structural recovery diagnostic ===" | tee -a "$log_path"
    cat "$diagnostic_path" | tee -a "$log_path"
    printf '\n%s\n' "=== End structural diagnostic ===" | tee -a "$log_path"
  fi
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
