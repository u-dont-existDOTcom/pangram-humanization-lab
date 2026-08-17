# Pangram GUI Browserbase Runbook

This workflow automates the authenticated Pangram web GUI when the direct Pangram API route is unavailable or when GUI/PDF segmentation is specifically desired.

It is measurement tooling only. It does not edit article prose and does not promote detector output to article authority.

## What it does

For each exact UTF-8 input file, the runner:

1. computes its SHA-256 and word count;
2. refuses to rerun a completed identical SHA or an ambiguous prior post-submit failure with the same runner unless `--force` is explicit;
3. opens Pangram's authenticated `/dashboard` inside a Browserbase cloud Chromium session using a persistent Context;
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

Open the Live View URL and log into Pangram normally. Do not return to the terminal while the Live View is still on `/login`: wait until it leaves that route and shows the detector dashboard, then press Enter. The runner first checks authenticated `/dashboard` tabs opened during login, then falls back to navigating the original tab to `/dashboard`. It rejects login/signup routes and visible account walls and verifies that the authenticated detector input is visible before it closes the Browserbase session. Bootstrap disables Browserbase keep-alive while retaining the active Playwright connection, so closing or disconnecting ends the session and triggers Context persistence instead of leaving a billable session running.

After successful verification, the CLI saves the non-secret Context ID at
`~/.config/pangram-gui/browserbase-context-id` with mode `0600`. Later local
`bootstrap` and `run` commands reuse it automatically; an explicit
`BROWSERBASE_CONTEXT_ID` still takes precedence. For GitHub Actions, create
these repository secrets:

- `BROWSERBASE_API_KEY`
- `BROWSERBASE_CONTEXT_ID`

There is no `BROWSERBASE_PROJECT_ID` secret or placeholder in this workflow.

Verify cross-session persistence before any detector submission:

```bash
python scripts/pangram_gui_browserbase.py verify
```

`verify` opens the saved Context in a fresh session and checks the authenticated detector input. It does not fill text or click Pangram's detector action.

## Recover an existing History report

If a detector submission completed in Pangram but the local runner was interrupted before writing evidence, do not submit it again. Recover the existing report instead:

```bash
python scripts/pangram_gui_browserbase.py recover --input <exact-input-path>
```

The command opens a non-keep-alive Browserbase session and prints a Live View URL. In Live View, select the matching existing report from Pangram History, then press Enter in the terminal. Recovery binds the report to stable leading/trailing anchors from the exact input, requires parsed word counts to match, and writes the normal body/PDF/result evidence with `evidence_source: recovered_existing_report` and `detector_submission_attempted: false`. It supports both the older segmented report layout and the current bounded short-text Overview layout (`AI Generated`, scanned word count, explicit entire-text statement, and `100% of this text is AI`). It never fills detector text or clicks the detector action.

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

A completed identical SHA is returned as cached. A failure recorded after the detector button was invoked is treated as an ambiguous submission and is not repeated automatically. To intentionally repeat one of those measurements after reviewing its session/result evidence:

```bash
python scripts/pangram_gui_browserbase.py run --force
```

Do not use `--force` simply because a previous result was inconvenient or timed out.

## Result artifacts

A successful measurement directory contains:

- `result.json` — exact input hash/word count, parsed summary/segments, Browserbase session references, report URL, PDF provenance;
- `report-body.txt` — raw visible Pangram report text used by the parser;
- `report.pdf` — Pangram native downloaded report when available, otherwise browser-print fallback.

A failed measurement contains:

- `failure.json` — failure stage, exception, exact input SHA, Browserbase session/debug/recording references;
- `failure.png` — best-effort full-page screenshot.

`failure.json` records whether detector submission was attempted. Pre-submit failures can be retried after the underlying issue is fixed. Post-submit failures require evidence review and explicit `--force`, because Pangram may already have accepted the text.

## Debugging failures

The first place to look is the Browserbase session/recording URL in `failure.json`. Browserbase records sessions by default, so UI drift and expired login state can be inspected without guessing.

Common failure stages:

- Browserbase `HTTP 401`: the API rejected the supplied API key before Context/session work; copy a current key and retry. Do not add a Project ID.
- disconnected bordered DevTools page: use the fullscreen Live View printed by the current runner or the active Session Inspector; older runner versions selected `debuggerUrl` instead of `debuggerFullscreenUrl`.

- `navigate`: Pangram or Browserbase navigation failed;
- `verify_authentication`: the saved Context reached login/signup, an account wall, or no bounded detector input on the authenticated dashboard;
- `fill_input`: detector input no longer accepts Playwright `fill()`;
- `submit`: Pangram's detection button name/UI changed;
- `wait_report`: report did not finish within the bounded timeout;
- `capture_body`: report rendered but structured text could not be recovered;
- `capture_pdf`: both native PDF attempt and print fallback failed.

The runner deliberately refuses broad selectors such as "click the first button". If Pangram changes its UI, update and test the bounded selectors rather than making them indiscriminate.

## Current live-verification status

Browserbase API-key inference, Context/session creation, CDP connection, fullscreen Live View, and Context-ID persistence have run successfully. A live smoke attempt exposed and preserved a false-authentication failure: the old runner used Pangram's public marketing page, clicked its public check control, and reached `/signup` rather than a report. The current runner targets `/dashboard`, rejects login/signup/account-wall states before filling text, and refuses automatic repetition of that ambiguous post-submit hash.

Authenticated cross-session Pangram persistence is now live-verified: the corrected bootstrap completed and the read-only `verify` command reached the authenticated detector in a fresh session, then closed normally without submitting text. One authorized 121-word smoke submission completed in Pangram and appears in History, but the local runner was interrupted with exit code `130` before it wrote evidence. Do not submit that hash again; use `recover` to capture the existing History report. Current structured segment parsing and native-download behavior remain uncertified until recovery succeeds.

Do not call the GUI automation fully verified until that live smoke test succeeds.
