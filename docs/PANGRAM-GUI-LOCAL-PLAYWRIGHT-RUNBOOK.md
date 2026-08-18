# Pangram GUI local Playwright runbook

This is the primary low-cost Pangram GUI transport for Joel's Zorin machine. It drives a **dedicated local persistent Chromium-family profile** through Playwright while reusing the exact-hash cache, ambiguity guard, bounded Pangram selectors, report parser, PDF/screenshot capture, and History-recovery logic already established by the Browserbase runner.

It is detector tooling only. It does not edit Romance prose or establish article authority. Browserbase remains an optional remote fallback.

## Safety model

- Default profile: `~/.config/pangram-local-browser/`.
- Default mode: **headed**; the browser window remains visible.
- Joel's normal Brave/Chromium/Chrome profile is refused unless the dangerous explicit override is supplied.
- A profile under any Git repository is refused unless the dangerous explicit override is supplied.
- Cookies, browser storage, passwords, API keys, and session tokens are never repository evidence.
- `verify` and `recover` never fill detector text or click the detector action.
- Exact completed results are cache hits across local and Browserbase transports.
- A failure after the detector action may have been invoked creates an ambiguous-submission block. Normal reruns stop before a browser opens.
- Every new complete result or failure is committed and pushed before another input can be submitted. A push failure preserves local evidence and blocks further paid work.

## Install on Joel's machine

From the repository branch containing this implementation:

```bash
python -m pip install -e '.[test,browser]'
```

The runner first looks for an already-installed browser in standard locations, preferring Brave on Joel's system (`/opt/brave.com/brave/brave`). Set an explicit executable only when discovery fails:

```bash
export PANGRAM_LOCAL_BROWSER=/opt/brave.com/brave/brave
```

Do not install Playwright's bundled Chromium merely by habit. Use the existing system browser when the launch smoke succeeds.

## 1. Environment and visible-window smoke

This command does not require Pangram authentication, article source recovery, or a GitHub push:

```bash
pangram-local status --environment-only --launch-smoke
```

It launches a simple page in the dedicated headed profile, waits for confirmation in the terminal, and closes the browser cleanly. The receipt reports Python, Playwright, display/session variables, browser executable, headed state, and profile path.

Equivalent script form:

```bash
python scripts/pangram_local.py status --environment-only --launch-smoke
```

## 2. One-time Pangram login

```bash
pangram-local bootstrap
```

A visible dedicated browser opens at Pangram login. Complete login manually. When the authenticated detector dashboard is visible, return to the terminal and press Enter. The runner verifies the bounded authenticated detector input and closes the context, allowing the dedicated profile to persist.

No Pangram password is stored in Git, environment files, or source code.

## 3. Fresh read-only authentication check

```bash
pangram-local verify
```

This launches a new persistent-context instance from the saved profile, navigates to the authenticated dashboard, checks that the detector input is editable, and closes. It does not fill text or activate Pangram's detector.

A combined environment/authentication receipt is also available:

```bash
pangram-local status --environment-only --check-auth
```

## 4. Inspect the exact current Romance inputs

With no explicit `--input`, `status` and `run` fetch the current Romance branch and materialize the two detector halves into a private cache under `~/.cache/pangram-local/inputs/<commit>/`.

Source branch:

`agent/romance-primal-crucible-gui-repair-20260817`

Authorized detector boundary:

- reader-visible total: **20,496 words**
- reader-visible SHA-256: `10359ab2119ffbe9a8a7a4a52cd0c3216bb1a6a2c0bffbd7e66fca01287f17ce`
- Part 1: **10,236 words**; SHA-256 `ae88df0f4156537239cb984337196703b88629c3588a5e58ee50c0888d3b39f8`
- Part 2: **10,260 words**; SHA-256 `2df878093bc05fefa98ca30e9a97bdd52e212370f432bf0408e90f1b60c54bb0`

The runner validates the live manifest, exact blob hashes, and exact word counts before opening the browser. The branch may advance only if those exact authorized identities remain unchanged; the actual fetched source commit is recorded in every result.

Read-only status:

```bash
pangram-local status
```

This reports source commit, exact identities, cache state, and any ambiguity block. It does not submit text.

## 5. Submit the current exact halves

Only after the headed smoke, bootstrap, read-only verification, and status checks succeed:

```bash
pangram-local run
```

Before opening the browser, the command:

1. fetches and verifies the exact current source boundary;
2. checks completed-result and ambiguous-submission state;
3. pushes existing evidence or the current branch head to GitHub;
4. opens the dedicated authenticated local profile.

For each uncached input it fills exact text, activates only a bounded detector action, waits for a bounded report marker, validates parsed word counts, captures raw report text and PDF evidence, writes a structured receipt, and commits/pushes that exact evidence directory before proceeding.

Do **not** use `--force` for the current halves. Neither exact current SHA has a prior Pangram submission in the recorded state.

## Explicit inputs

The current Romance halves are the safe default. Other inputs can be supplied explicitly:

```bash
pangram-local run \
  --input /path/to/part.txt \
  --expect-sha part.txt=<64-character-sha256>
```

Repeat both flags for multiple files. Supplying exact SHA gates is strongly preferred for any paid call.

## Recover an existing History report without resubmission

For one of the current Romance parts:

```bash
pangram-local recover --part 1
pangram-local recover --part 2
```

For another exact file:

```bash
pangram-local recover \
  --input /path/to/exact-input.txt \
  --expect-sha exact-input.txt=<64-character-sha256>
```

The runner opens Pangram without filling text. Select the matching report in History and press Enter in the terminal. Recovery binds visible report anchors and parsed word count to the exact input, captures normal evidence, marks `detector_submission_attempted: false`, and pushes the result.

## Evidence layout and provenance

Evidence remains content-addressed under:

`state/gui-runs/pangram-4/<input-sha256>/`

A complete result contains:

- `result.json`
- `report-body.txt`
- `report.pdf`

A failure contains:

- `failure.json`
- `failure.png` when screenshot capture succeeds

Local receipts distinguish:

- shared cache identity and Pangram model;
- `transport: local_playwright`;
- local transport runner version;
- dedicated profile kind and non-secret path label;
- browser executable, headed state, Playwright version, and platform;
- exact input SHA and word count;
- source repository, branch, commit, source path, manifest hash, and reader-visible SHA for the current Romance halves;
- detector version and report layout when visible;
- raw-report and PDF SHA-256;
- native Pangram download, Playwright print fallback, or local CDP print fallback provenance;
- whether a detector submission was attempted.

## Failure semantics

### Before detector activation

Authentication, selector, fill, source, SHA, Git, or launch failures before the detector action may be retried after repair. The saved receipt states `detector_submission_attempted: false`.

### At or after detector activation

The runner sets the ambiguity boundary immediately before activating the bounded detector control. Any subsequent failure is treated as potentially paid/accepted. It saves and pushes the failure, stops the batch, and refuses an automatic repeat of that SHA. Check Pangram History and use `recover` first.

### Git push failure

A complete result or ambiguous failure remains locally cache-blocking even when its Git push fails. The command stops. On the next invocation, preflight syncs that existing evidence before any new detector action.

## Browserbase fallback

The Browserbase implementation remains documented in `PANGRAM-GUI-BROWSERBASE-RUNBOOK.md`. Both transports share exact result identity, parser, selector, cache, PDF, and ambiguity semantics. Browserbase should be used only when a remote browser is materially useful and account capacity is available.

## Current certification boundary

The deterministic implementation and repository tests can certify code behavior without a Pangram charge. The following require Joel's actual Zorin desktop/session and remain separate live gates:

- a visible headed launch with the installed Brave/Chromium executable;
- one-time manual Pangram login in the dedicated profile;
- fresh cross-process authentication persistence;
- current long-document Pangram report layout and PDF behavior;
- the two paid exact Romance submissions.

Do not describe those live surfaces as verified until their receipts exist.
