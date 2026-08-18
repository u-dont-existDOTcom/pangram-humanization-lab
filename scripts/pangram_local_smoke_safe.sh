#!/usr/bin/env bash

# Diagnostic wrapper deliberately avoids strict-mode shell options. It must
# return control to the operator even when the browser smoke itself fails.
set +e

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$repo_root" ]; then
  printf '%s\n' "ERROR: run this from inside the pangram-humanization-lab Git checkout."
  exit 0
fi

cd "$repo_root" || {
  printf '%s\n' "ERROR: could not enter repository: $repo_root"
  exit 0
}

runner="$repo_root/.venv/bin/pangram-local"
if [ ! -x "$runner" ]; then
  printf '%s\n' "ERROR: $runner is missing or not executable."
  printf '%s\n' "Install inside the repository virtual environment first:"
  printf '%s\n' ".venv/bin/python -m pip install -e '.[test,browser]'"
  exit 0
fi

log_dir="${HOME}/Téléchargements"
mkdir -p "$log_dir"
log_path="$log_dir/pangram-local-smoke.log"

printf '%s\n' "=== Pangram local environment ===" | tee "$log_path"
"$runner" status --environment-only 2>&1 | tee -a "$log_path"
env_rc=${PIPESTATUS[0]}
printf '\nENVIRONMENT_EXIT=%s\n\n' "$env_rc" | tee -a "$log_path"

printf '%s\n' "=== Pangram local headed launch smoke ===" | tee -a "$log_path"
"$runner" status --environment-only --launch-smoke 2>&1 | tee -a "$log_path"
smoke_rc=${PIPESTATUS[0]}
printf '\nSMOKE_EXIT=%s\nLOG=%s\n' "$smoke_rc" "$log_path" | tee -a "$log_path"

if [ "$smoke_rc" -eq 0 ]; then
  printf '%s\n' "SMOKE_RESULT=pass"
else
  printf '%s\n' "SMOKE_RESULT=failed_but_terminal_preserved"
fi

# This is a diagnostic wrapper, not a CI gate. Return success so an inherited
# interactive `set -e` cannot close the operator's terminal after diagnostics.
exit 0
