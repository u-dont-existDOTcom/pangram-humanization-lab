# Pangram GUI local Playwright runbook

This is the primary local Pangram GUI transport for Joel's Zorin machine. It drives a **dedicated persistent Chromium-family profile** through Playwright while preserving exact input identity, cache/ambiguity guards, paid-call accounting, evidence capture, bounded tabs, and GitHub durability.

It is detector tooling only. It does not edit Romance prose or establish article authority. Browserbase remains an optional remote fallback.

## Safety model

- Default profile: `~/.config/pangram-local-browser/`.
- Default mode: **headed**; the browser window remains visible.
- The ordinary Brave/Chromium/Chrome profile is refused unless a dangerous explicit override is supplied.
- A profile under a Git repository is refused unless a dangerous explicit override is supplied.
- Chromium sandboxing is explicitly enabled for the authenticated persistent profile.
- Cookies, browser storage, passwords, API keys, raw history API records, and session tokens are never repository evidence.
- Read-only verification/recovery never fills detector text or clicks the detector action.
- Exact completed results are content-addressed cache hits.
- A failure after detector activation may have occurred creates an ambiguity block; normal reruns stop before another paid click.
- Paid-call reservations are committed/pushed before the detector click.
- Every new complete result or ambiguous failure is committed/pushed before another input may proceed.
- Persistent browser state is for authentication, not tab accumulation: normal runs close extras and leave one inert tab on shutdown.

## Install / runtime

Use the repository virtual environment; do not install into the system Python.

```bash
python -m pip install -e '.[test,browser]'
```

The runner prefers the installed Brave executable on the owner machine:

`/opt/brave.com/brave/brave`

Set `PANGRAM_LOCAL_BROWSER` only if normal discovery fails.

## 1. Environment and visible-window smoke

```bash
pangram-local status --environment-only --launch-smoke
```

This is non-paid. It checks the dedicated profile, browser executable, Playwright environment, visible launch, and clean context close.

## 2. One-time Pangram login

```bash
pangram-local bootstrap
```

Complete login manually in the dedicated browser. No password or authentication material is written to Git.

## 3. Fresh read-only authentication check

```bash
pangram-local verify
```

The check waits for the hydrated authenticated detector surface and verifies the input without filling or submitting text.

## 4. Exact current Romance boundary

Current source branch:

`agent/romance-primal-crucible-gui-repair-20260817`

Authorized reader-visible boundary:

- total: **20,496 words**; SHA-256 `10359ab2119ffbe9a8a7a4a52cd0c3216bb1a6a2c0bffbd7e66fca01287f17ce`
- Part 1: **10,236 words**; SHA-256 `ae88df0f4156537239cb984337196703b88629c3588a5e58ee50c0888d3b39f8`
- Part 2: **10,260 words**; SHA-256 `2df878093bc05fefa98ca30e9a97bdd52e212370f432bf0408e90f1b60c54bb0`

Default source materialization reads the manifest and part blobs from the live source branch and verifies exact hashes/word counts before browser work.

Read-only status remains available through:

```bash
pangram-local status
```

## 5. Current Romance paid/recovery state

Audit:

`romance-current-20496-pangram-gui-20260818`

### Part 1: one paid call, ambiguous — DO NOT REPEAT

Part 1 was submitted once. The original runner then captured the initiating dashboard instead of binding the result to the exact stored document. Its failure receipt records `detector_submission_attempted: true`, and its paid-call reservation remains durable.

**Do not run generic `pangram-local run`, do not use `--force`, and do not resubmit Part 1.** Recover the existing paid record first.

### Part 2: never submitted

Part 2 has no paid reservation and remains blocked until Part 1 is recovered exactly.

## 6. Current long-document report contract

Live owner-machine diagnostics on 2026-08-19 established the current Pangram long-document surfaces:

- report page: `https://www.pangram.com/history/<uuid>`;
- stored record API: `https://web.pangram.com/api/history/<uuid>/`;
- history list API: `https://web.pangram.com/api/history-list/`;
- current overview exposes document-level Human/AI percentages and paginated highlights rather than the old per-segment word-count headings.

The legacy segmented DOM parser is therefore not authoritative for current long documents.

### Exact record identity

A result is bound to an input only when the read-only stored history API record itself contains the literal submitted text. The runner verifies and records:

- exact UTF-8 text SHA-256;
- exact word count;
- the JSON field path containing the exact text;
- non-secret model/prediction metadata needed for provenance.

Raw API records are processed only in memory and are not committed.

### Score parsing

Human/AI fractions are parsed from the exact record's rendered report overview. Although the API record exposes `prediction` and `prediction_prob`, their probability semantics were not established by the live diagnostic. The runner therefore **does not infer score fractions from `prediction_prob`**. If rendered percentages cannot be parsed, it fails closed.

No synthetic segment list or invented segment word counts are created.

## 7. Safe current Romance operator command

Use the repository-owned terminal-safe wrapper:

```bash
bash scripts/pangram_local_romance_recover_resume_safe.sh
```

The wrapper:

1. `git pull --ff-only` and re-execs exactly once if the pull changed the wrapper itself;
2. runs the complete local deterministic suite;
3. attempts **read-only exact stored-record recovery of Part 1** through `pangram_local_romance_recover_part1_api.py`;
4. refuses to proceed if Part 1 cannot be exact-bound;
5. persists/caches the recovered Part-1 receipt when successful;
6. only then invokes `pangram_local_romance_paid_api.py --execute`, where Part 1 is a cache hit and only Part 2 may be new;
7. attaches the exact-history response listener before any Part-2 detector click;
8. reserves and Git-pushes the Part-2 call before the click;
9. accepts Part 2 only after its newly stored history record exact-matches the submitted Part-2 text;
10. captures report body/PDF evidence and pushes the completed receipt before exit.

If Part 2 is clicked but its exact stored record cannot be bound, the run stops as ambiguous. Never repeat it automatically.

## 8. Generic explicit inputs

Generic explicit-input support remains available for other work, but it is **not the current Romance recovery path**:

```bash
pangram-local run \
  --input /path/to/part.txt \
  --expect-sha part.txt=<64-character-sha256>
```

Use exact SHA gates for paid calls. Do not use generic execution to bypass a content-addressed cache, ambiguity block, or paid reservation.

## 9. Evidence layout

Evidence remains content-addressed under:

`state/gui-runs/pangram-4/<input-sha256>/`

A complete result contains:

- `result.json`
- `report-body.txt`
- `report.pdf`

A failure contains:

- `failure.json`
- `failure.png` when screenshot capture succeeds

Receipts preserve, as applicable:

- exact input SHA and word count;
- source repository/branch/commit/path/manifest provenance;
- local Playwright transport and browser provenance;
- paid-call accounting;
- exact stored-history-record proof (without raw record content);
- rendered Human/AI summary;
- raw-report/PDF hashes and PDF capture provenance;
- whether detector activation was attempted.

## 10. Failure semantics

### Before detector activation

Authentication, source, SHA, selector, fill, Git, or launch failures before the detector action can be repaired/retried. The receipt records `detector_submission_attempted: false`.

### At or after detector activation

The ambiguity boundary is set immediately before the detector action. Any later failure is potentially paid/accepted. Save/push the failure and recover the existing stored record before any repeat.

### Git push failure

A complete result or ambiguous failure remains locally blocking even if the push fails. The next invocation must sync existing evidence before new paid work.

## 11. Browserbase fallback

Browserbase remains an optional fallback documented in `PANGRAM-GUI-BROWSERBASE-RUNBOOK.md`. Do not move an ambiguous exact SHA to another transport merely to bypass the ambiguity guard.

## 12. Persistent Chat-triggered bridge

Explicit GUI checks no longer require Joel to open a Work task or type local commands once `pangram-gui-bridge.service` is installed. Chat appends a schema-valid immutable data request on `automation/pangram-gui-bridge-queue`; the graphical-session daemon invokes this same headed local Playwright/Brave transport and publishes durable evidence on `agent/pangram-local-playwright-gpt-20260818`.

The bridge does not add a detector stack, API substitution, or autonomous rewriting. It composes the existing exact cache, paid reservation, read-only History recovery, ambiguity protection, evidence capture, and `GitSync` behavior. Its fixed schema, trusted source/extraction registry, branch topology, service runbook, result shape, and enqueue instructions are in `PANGRAM-GUI-BRIDGE.md`.

## Current certification boundary

Repository tests certify deterministic code behavior without a Pangram charge. Owner-machine live verification is still required for actual authenticated recovery/submission and current report rendering. A bridge `verify` request is the read-only headed authentication gate. Paid work remains separately authorized and preservation-gated.
