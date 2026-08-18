#!/usr/bin/env bash

# Local owner-machine verification gate. Deliberately does not enable strict
# mode in the caller's shell and always returns control to the terminal.
set +e

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$repo_root" ]; then
  printf '%s\n' "ERROR: run this from inside the pangram-humanization-lab checkout."
  exit 0
fi

cd "$repo_root" || {
  printf '%s\n' "ERROR: could not enter repository: $repo_root"
  exit 0
}

python="$repo_root/.venv/bin/python"
runner="$repo_root/.venv/bin/pangram-local"
if [ ! -x "$python" ] || [ ! -x "$runner" ]; then
  printf '%s\n' "ERROR: repository virtual environment or pangram-local executable is missing."
  exit 0
fi

log_dir="${HOME}/Téléchargements"
mkdir -p "$log_dir"
log_path="$log_dir/pangram-local-postlogin.log"

printf '%s\n' "=== Local deterministic gate ===" | tee "$log_path"
"$python" -m pytest -q 2>&1 | tee -a "$log_path"
test_rc=${PIPESTATUS[0]}
printf '\nLOCAL_TEST_EXIT=%s\n' "$test_rc" | tee -a "$log_path"

if [ "$test_rc" -ne 0 ]; then
  printf '%s\n' "POSTLOGIN_RESULT=local_tests_failed" | tee -a "$log_path"
  printf 'LOG=%s\n' "$log_path" | tee -a "$log_path"
  exit 0
fi

printf '\n%s\n' "=== Fresh-process Pangram authentication verification ===" | tee -a "$log_path"
"$runner" verify 2>&1 | tee -a "$log_path"
verify_rc=${PIPESTATUS[0]}
printf '\nVERIFY_EXIT=%s\n' "$verify_rc" | tee -a "$log_path"

if [ "$verify_rc" -ne 0 ]; then
  printf '%s\n' "POSTLOGIN_RESULT=verify_failed_no_submission" | tee -a "$log_path"
  if [ -f "$log_dir/pangram-local-auth-diagnostic.json" ]; then
    printf 'AUTH_DIAGNOSTIC_JSON=%s\n' "$log_dir/pangram-local-auth-diagnostic.json" | tee -a "$log_path"
  fi
  if [ -f "$log_dir/pangram-local-auth-diagnostic.png" ]; then
    printf 'AUTH_DIAGNOSTIC_SCREENSHOT=%s\n' "$log_dir/pangram-local-auth-diagnostic.png" | tee -a "$log_path"
  fi
  printf 'LOG=%s\n' "$log_path" | tee -a "$log_path"
  exit 0
fi

printf '\n%s\n' "=== Exact current Romance read-only status ===" | tee -a "$log_path"
"$runner" status 2>&1 | tee -a "$log_path"
status_rc=${PIPESTATUS[0]}
printf '\nSTATUS_EXIT=%s\n' "$status_rc" | tee -a "$log_path"

if [ "$status_rc" -eq 0 ]; then
  printf '%s\n' "POSTLOGIN_RESULT=ready_for_paid_gate_review" | tee -a "$log_path"
else
  printf '%s\n' "POSTLOGIN_RESULT=status_failed_no_submission" | tee -a "$log_path"
fi
printf 'LOG=%s\n' "$log_path" | tee -a "$log_path"

# Diagnostic/verification wrapper, not a CI gate. Never close the caller's
# interactive terminal because a child command returned nonzero.
exit 0
