# Pangram GUI Browserbase Runbook

This workflow automates the authenticated Pangram web GUI when the direct Pangram API route is unavailable or when GUI/PDF segmentation is specifically desired.

It is measurement tooling only. It does not edit article prose and does not promote detector output to article authority.

## What it does

For each exact UTF-8 input file, the runner:

1. computes its SHA-256 and word count;
2. refuses to rerun a completed identical SHA with the same runner unless `--force` is explicit;
3. opens Pangram inside a Browserbase cloud Chromium session using a persistent Context;
4. pastes the exact text into Pangram's detector;
5. waits for the Pangram report;
6. records the GUI report body and parses summary/segment labels, word counts and confidence;
7. downloads a native Pangram PDF when a clearly named PDF/report download control is available, otherwise records a Playwright print-to-PDF fallback with different provenance;
8. records Browserbase session/debug/recording URLs so a failed or surprising run can be inspected.

Results are content-addressed under:

`state/gui-runs/pangram-4/<input-sha256>/`

## Prerequisites

- A Browserbase account with an API key.
- Python 3.10+.
- Pangram GUI access through your normal Pangram account.

Browserbase resolves the project from the API key. Do not set or request `BROWSERBASE_PROJECT_ID` for this runner.

Install this repository with browser support:

```bash
python -m pip install -e '.[test,browser]'
```

The runner connects to Browserbase's Chromium over CDP; it does not launch a local Chromium instance for detector runs.

## One-time Pangram login bootstrap

Do **not** put a Pangram password in GitHub secrets or repository files.

Set the Browserbase API key locally:

```bash
export BROWSERBASE_API_KEY='...'
```

If you already have a Context you want to reuse, you may also set:

```bash
export BROWSERBASE_CONTEXT_ID='...'
```

Otherwise bootstrap creates a new Context using the API key alone.

Run:

```bash
python scripts/pangram_gui_browserbase.py bootstrap
```

The command prints:

- a Browserbase Context ID;
- a fullscreen Live View URL intended for human control.

Open the Live View URL, log into Pangram normally, return to the terminal, and press Enter. The runner verifies that Pangram's detector input is visible before it closes the Browserbase session. Context changes are persisted when that session closes.

After successful verification, the CLI saves the non-secret Context ID at
`~/.config/pangram-gui/browserbase-context-id` with mode `0600`. Later local
`bootstrap` and `run` commands reuse it automatically; an explicit
`BROWSERBASE_CONTEXT_ID` still takes precedence. For GitHub Actions, create
these repository secrets:

- `BROWSERBASE_API_KEY`
- `BROWSERBASE_CONTEXT_ID`

There is no `BROWSERBASE_PROJECT_ID` secret or placeholder in this workflow.

## Local unattended run

Set the API key:

```bash
export BROWSERBASE_API_KEY='...'
```

The runner reads the Context ID saved by the successful bootstrap. Set
`BROWSERBASE_CONTEXT_ID` only to intentionally override that local Context.

Then run the current Romance halves:

```bash
python scripts/pangram_gui_browserbase.py run
```

Or explicit files:

```bash
python scripts/pangram_gui_browserbase.py run \
  --input work/romance-current-assembly/pangram-part-1.txt \
  --input work/romance-current-assembly/pangram-part-2.txt
```

A completed identical SHA is returned as cached. To intentionally repeat the same GUI measurement:

```bash
python scripts/pangram_gui_browserbase.py run --force
```

Do not use `--force` simply because a previous result was inconvenient.

## Result artifacts

A successful measurement directory contains:

- `result.json` — exact input hash/word count, parsed summary/segments, Browserbase session references, report URL, PDF provenance;
- `report-body.txt` — raw visible Pangram report text used by the parser;
- `report.pdf` — Pangram native downloaded report when available, otherwise browser-print fallback.

A failed measurement contains:

- `failure.json` — failure stage, exception, exact input SHA, Browserbase session/debug/recording references;
- `failure.png` — best-effort full-page screenshot.

A failed run does not create a completed `result.json`, so it can be resumed after the underlying issue is fixed.

## Debugging failures

The first place to look is the Browserbase session/recording URL in `failure.json`. Browserbase records sessions by default, so UI drift and expired login state can be inspected without guessing.

Common failure stages:

- Browserbase `HTTP 401`: the API rejected the supplied API key before Context/session work; copy a current key and retry. Do not add a Project ID.
- disconnected bordered DevTools page: use the fullscreen Live View printed by the current runner or the active Session Inspector; older runner versions selected `debuggerUrl` instead of `debuggerFullscreenUrl`.

- `navigate`: Pangram or Browserbase navigation failed;
- `find_input`: Pangram login likely expired or the detector UI changed;
- `fill_input`: detector input no longer accepts Playwright `fill()`;
- `submit`: Pangram's detection button name/UI changed;
- `wait_report`: report did not finish within the bounded timeout;
- `capture_body`: report rendered but structured text could not be recovered;
- `capture_pdf`: both native PDF attempt and print fallback failed.

The runner deliberately refuses broad selectors such as "click the first button". If Pangram changes its UI, update and test the bounded selectors rather than making them indiscriminate.

## Current live-verification status

The parser, identity, duplicate-defense, Browserbase REST lifecycle, and orchestration are testable without credentials. The actual Pangram GUI selectors and native-download behavior cannot be certified until a real Browserbase Context is configured and a one-time Pangram login bootstrap is performed.

Do not call the GUI automation fully verified until that live smoke test succeeds.
