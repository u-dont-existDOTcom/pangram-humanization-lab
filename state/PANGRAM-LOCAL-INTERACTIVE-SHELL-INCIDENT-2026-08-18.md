# Pangram local Playwright — interactive-shell setup incident — 2026-08-18

Status: setup/diagnostic incident; no Pangram detector submission occurred.

## Owner report

After the local Playwright checkout/venv setup instructions were run, the command:

```bash
.venv/bin/pangram-local status --environment-only --launch-smoke
```

caused the terminal window/session to disappear before a useful smoke-test error could be captured.

The immediately preceding assistant-supplied setup block had begun with:

```bash
set -e
```

and was pasted directly into the user's interactive shell.

## Diagnosis

`set -e`/`errexit` changes shell state. When supplied as a standalone interactive-shell command, that state can persist after the setup block finishes. A later nonzero command can therefore terminate the interactive shell instead of simply returning control to the prompt.

The current Pangram smoke implementation in `src/pangram_lab/gui_local.py` launches a persistent Playwright context, opens a local `data:` page, optionally waits for Enter, closes the context, and returns a receipt. It does not contain a mechanism for terminating its parent shell. Therefore the terminal disappearance is attributed to the leaked interactive-shell `errexit` state, while the **underlying reason that the smoke command returned nonzero remains unresolved** because its diagnostic output was lost.

Do not infer from this incident that Playwright, Brave, the dedicated profile, or Pangram authentication is itself broken. Those remain to be tested in a shell whose failure policy is not modified persistently.

## Corrective rule

Never paste `set -e`, `set -u`, `set -o pipefail`, traps, changed shell options, exported failure-sensitive hooks, or similar persistent shell-state mutations into a user's ordinary interactive terminal as part of a copy/paste setup block unless the block restores the prior shell state on every path.

Prefer one of these boundaries:

1. put strict-mode setup inside a repository script executed as a child process;
2. run it in an explicit subshell `( set -euo pipefail; ... )` so options die with the subshell; or
3. use ordinary stepwise commands with explicit error checks when the user must remain in the same interactive shell.

For live diagnostics, preserve the terminal and the failure evidence. A diagnostic wrapper may intentionally capture the child command's exit status and output while itself returning normally; a verification gate may still fail nonzero, but should not depend on hidden interactive-shell state.

## Immediate recovery

A newly opened terminal starts without the leaked `errexit` state under normal Bash defaults. If continuing in an existing affected shell, run:

```bash
set +e
```

before diagnostic commands.

The next smoke attempt should capture both stdout/stderr and the child exit status so the actual browser-launch failure, if any, can be diagnosed without another disappearing terminal.

## Scope

This is not a Pangram detector-science or humanization lesson. It is a transferable CLI/bootstrap/interactive-shell safety lesson and should be promoted to `u-dont-existDOTcom/universal-dev-architecture`; Pangram keeps this exact incident as project-local provenance.
