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

## Live Zorin receipt — 2026-08-18

Owner-machine evidence confirmed a successful visible headed launch using:

- Brave: `/opt/brave.com/brave/brave`;
- Playwright: `1.62.0`;
- Python: `3.12.3` inside the repository virtual environment;
- Wayland session with `DISPLAY=:0`;
- dedicated profile: `~/.config/pangram-local-browser`;
- clean persistent-context close;
- no Pangram authentication and no detector submission.

The first guard failure was caused by a stale/inert `$HOME/.git` marker. The hardened guard ignores an inert marker only at the actual home root; valid Git worktrees remain blocked, and unresolved `.git` markers elsewhere remain conservatively blocked.

The first visible Brave smoke also exposed Playwright's documented Chromium default of disabled sandboxing (`chromium_sandbox=false`), which caused Brave to show a `--no-sandbox` warning. Before any authenticated Pangram profile is created, the local transport must request `chromium_sandbox=True` and re-pass the visible smoke without that warning.

The repository-side suite passed **161 tests** before this hardening pass. The hardening pass adds regressions for the inert-home-marker exception, real Git-worktree blocking, and Chromium sandbox enablement; use the exact-head CI receipt rather than the historical count as the current code gate.

The exact originating shell-state incident and its disposition are preserved in `state/PANGRAM-LOCAL-INTERACTIVE-SHELL-INCIDENT-2026-08-18.md` and the canonical lesson ledger. The local-Playwright current-state checkpoint, inherited Browserbase free-minute blocker, and local-Playwright handoff also have their required `no-new-lesson` dispositions. The transferable shell-safety rule is merged into `u-dont-existDOTcom/universal-dev-architecture` as `patterns/interactive-shell-command-safety.md`.
