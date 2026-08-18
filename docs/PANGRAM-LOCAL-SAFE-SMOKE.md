# Pangram local Playwright — terminal-safe smoke

Use this path when diagnosing the local headed-browser launch on Joel's Zorin machine.

Do not put `set -e`, `set -u`, `set -o pipefail`, or traps into the operator's persistent interactive shell. The repository-owned diagnostic wrapper deliberately returns control to the terminal even when the child smoke command fails.

From the current local-Playwright checkout:

```bash
git pull --ff-only
bash scripts/pangram_local_smoke_safe.sh
```

The wrapper:

- confirms it is running inside the repository;
- requires the repository `.venv/bin/pangram-local` executable;
- records the read-only environment status;
- runs the headed launch smoke without any Pangram detector submission;
- captures stdout/stderr to `~/Téléchargements/pangram-local-smoke.log`;
- prints `ENVIRONMENT_EXIT`, `SMOKE_EXIT`, and a final `SMOKE_RESULT`;
- exits successfully as a diagnostic wrapper so inherited interactive `errexit` cannot terminate the operator shell.

A nonzero `SMOKE_EXIT` still means the browser smoke itself failed. Inspect or share the captured terminal output/log to diagnose the underlying Playwright/browser/session problem. Do not infer the child failure from the parent-terminal behavior.

The repository-side test suite for this branch passes **161 tests** after correcting the Playwright factory test fake. This does not certify the Zorin graphical smoke; that live browser/session boundary remains the purpose of this wrapper.

The exact originating shell-state incident and its disposition are preserved in `state/PANGRAM-LOCAL-INTERACTIVE-SHELL-INCIDENT-2026-08-18.md` and the canonical lesson ledger. The local-Playwright current-state checkpoint, inherited Browserbase free-minute blocker, and local-Playwright handoff also have their required `no-new-lesson` dispositions. The transferable shell-safety rule is merged into `u-dont-existDOTcom/universal-dev-architecture` as `patterns/interactive-shell-command-safety.md`.
