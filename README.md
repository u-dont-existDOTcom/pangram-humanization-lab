# Pangram Humanization Lab

Adaptive detector-research harness for Joel Rosenblum's humanization work.

**Current recovery authority is `state/CURRENT-STATE.md`.** As of 2026-08-20 the supported transport architecture is:

1. the owner's self-hosted Pangram API path for normal programmatic detector work;
2. `pangram-local`, a headed local Brave/Chromium + Playwright GUI fallback for authenticated History recovery, visual evidence, and resilience.

The older GitHub-hosted Actions detector route and remote Browserbase proposal are not the normal transport path. Do not infer current detector availability from their historical status.

## Current detector routing

### Self-hosted API — normal programmatic route

Use the owner's self-hosted Pangram execution path when a programmatic result is sufficient. Keep the repository's content-addressed cache, exact text hashes, task checkpoint/resume, model/version gates, paid-call accounting, and recovery-before-repeat rules around that transport. Never expose or commit API credentials.

### Local Playwright GUI — supported fallback

Use `pangram-local` when authenticated GUI/History inspection or visual evidence is useful:

```bash
pangram-local status --check-auth
pangram-local run --input path/to/text.txt
pangram-local recover --input path/to/text.txt
```

The local runner uses a dedicated persistent browser profile, writes a durable submission reservation before a paid click, binds completion to the exact stored Pangram History record, reads Pangram 4's structured `response.overall` result, and blocks automatic repeat after ambiguous work. See `docs/PANGRAM-LOCAL-PLAYWRIGHT.md`.

### GitHub Actions — legacy/optional route

The repository-secret fixed-batch workflow remains useful historical/optional infrastructure, but it is **not required to establish Pangram access**. A 2026-08-19 live test showed that the same valid API key could succeed locally while the Pangram async external endpoint returned HTTP 401 from GitHub-hosted runners. That compatibility issue is tracked in issue #95.

Do not automatically retry paid work through Actions after an ambiguous or rejected request. If a future task specifically needs GitHub-hosted detector execution, first verify the current endpoint/origin policy and read `docs/PANGRAM-ACTIONS-RUNBOOK.md`.

## One-command harness use on Joel's Zorin machine

The original v2.0.1 experiment installer remains available for the adaptive research harness. Unzip under `~/Téléchargements`, enter the folder, and run:

```bash
./INSTALL-AND-RUN.sh
```

With no arguments it looks for `AI.txt` and `HUMAN.txt` locally, then in the prior `pangram-experiment-harness-v1` directory. You may also pass the files explicitly:

```bash
./INSTALL-AND-RUN.sh AI.txt HUMAN.txt
```

The installer:

1. creates/updates `.venv`;
2. runs the deterministic test suite;
3. initializes Git and, when bootstrapping a fresh repository, creates/uses a private GitHub repository by default through the authenticated `gh` CLI;
4. copies the old autopilot's working lessons/controlled-test ledger when available;
5. imports reusable Pangram 4 results from prior harnesses/calibration folders;
6. prints the cache summary;
7. starts the adaptive experiment.

The canonical `u-dont-existDOTcom/pangram-humanization-lab` repository is currently **public by owner decision**. The installer's fresh-repository privacy default does not describe the visibility of the canonical repository.

No Pangram experiment begins until the initial GitHub backup succeeds. After that, each Codex artifact, task-id checkpoint, Pangram result, repeat, statistics file, and analysis artifact is committed and pushed. If GitHub becomes unavailable, the local file is saved first and the run stops before another paid detector submission.

## What you see while the adaptive harness runs

Codex output is streamed as it happens:

```text
[codex:designer] START ...
[codex:designer] ...tool/status output...
[codex:designer] … still working (30s)
[codex:designer] DONE ...
```

Pangram API work is similarly explicit:

```text
[pangram] CACHE HIT ...
[pangram] RESUME pending task ...; NO new POST
[pangram] SUBMIT new task ...
[pangram] CHECKPOINTED task_id=... before polling
[pangram] SAVED ...
```

## Duplicate-call defense

Base results are keyed by Pangram model + expected API result version + exact submitted-text SHA-256. Exact repeats use deterministic measurement identities. A completed matching record is reused. A pending task is resumed using its saved identity. An ambiguous paid action is **not** automatically repeated.

The importer reads the earlier `campaign-state.json`/raw-response form and the newer harness `state.json` form. Pangram 3 results are retained as historical evidence but never substituted for Pangram 4 calls.

The same invariant applies to the local GUI transport: if a reservation exists without a complete result, recover from authenticated Pangram History before considering another paid submission.

## Authorship-signal retention

Pangram status, editorial fidelity, and authorship-signal retention are separate results. A detector-Human passage can still be generic or unlike Joel, while a passage that resembles an author profile can still change his argument. The local idiolect commands add a non-billable third measurement axis for substantial rewriting:

```bash
pangram-lab idiolect-retention \
  --profile-dir path/to/private-reference-texts \
  --original original-visible-text.txt \
  --candidate candidate-visible-text.txt \
  --output idiolect-retention.json
```

For method-development work with multiple authors and aligned originals/rewrites:

```bash
pangram-lab idiolect-ier dataset.json --output closed-set-ier.json
```

The routine command is a **single-author retention proxy**, not Idiolect Erasure Rate. True IER requires a closed-set multi-author attribution benchmark. Reports contain hashes and aggregate measurements, not raw source text, and deliberately provide no universal pass threshold. See `docs/IDIOLECT-RETENTION-PROTOCOL.md` before using either command.

## GitHub and credentials

The canonical repository is public. API credentials are not. The code never authorizes retrieving or printing detector secrets. `.env`, key/secret files, browser auth profiles, and `.venv` must remain outside Git.

Current transport availability must be resolved from `state/CURRENT-STATE.md`, the exact cache/reservation/history state, and the supported transport documentation. A missing local environment variable, a signed-out ordinary browser, or a failed legacy Actions call does not by itself prove that Pangram is unavailable.

## Experimental contract

Human editorial quality, semantic sanity, fidelity, and article function outrank Pangram. Synthetic probes must preserve meaning. The blind reviewer runs before new Pangram measurements where the experiment protocol requires it. Controlled experiments use explicit factor assignments and deterministic statistics rather than phrase superstition.

Authorship-retention metrics are evidence, not editorial authority. Never add errors, fake specificity, memories, catchphrases, unusual punctuation, slang, or corpus tics to improve similarity. Use the minimum edit dose, preserve owner language and thought routes where available, and keep semantic/architecture review blocking.

## External async transport history

Target-machine evidence on 2026-08-12 showed that an async submission without a model selector could return terminal version `3.3.2`. The validated Pangram-4 harness explicitly requests `model: pangram-4`; an explicit Pangram-4 request that returns another version fails closed rather than automatically buying another call.

On 2026-08-19 the GitHub-hosted Actions environment exposed a separate origin-specific incompatibility: the same non-empty key authenticated locally and against another documented Pangram endpoint, while `https://text.external-api.pangram.com/task` returned HTTP 401 from GitHub-hosted runners before a task ID was issued. This is preserved in issue #95. It does not block the current self-hosted API or local GUI transports.

## Repository operations and recovery

Use `python -m pip install -e '.[test]'` as the non-interactive bootstrap and `python -m pytest -q` as the complete deterministic test gate. Run the repository-visible operating audit with:

```bash
python scripts/audit_codex_github.py --root . --fail-on error
```

Run the current lesson audit with:

```bash
PYTHONPATH=src python -m pangram_lab.lesson_closeout audit --ref HEAD
```

`./INSTALL-AND-RUN.sh` is a live interactive experiment path, not a bootstrap command. It can progress toward paid detector work after its GitHub, input, cache, and checkpoint gates. Do not run it for CI or repository compliance.

Recovery begins at `state/CURRENT-STATE.md`, lesson retrieval begins at `state/LESSON-INDEX.md`, and documentation routing begins at `docs/INDEX.md`. For local GUI operation read `docs/PANGRAM-LOCAL-PLAYWRIGHT.md`. Treat `docs/PANGRAM-ACTIONS-RUNBOOK.md` as legacy/optional transport documentation unless a task specifically requires GitHub-hosted detector execution.
