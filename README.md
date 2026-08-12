# Pangram Humanization Lab v2.0.1

Adaptive detector-research harness for Joel Rosenblum's humanization work.

This release deliberately reuses the **persistence/evidence model of the earlier working Pangram autopilot** instead of treating detector calls as disposable. It adds a Pangram-4 content-addressed cache, task-id checkpoint/resume, live Codex status streaming, strict structured-output contracts compatible with current Codex CLI, adaptive controlled experiments, and automatic private GitHub backup.

## One-command use on Joel's Zorin machine

Unzip under `~/Téléchargements`, enter the folder, and run:

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
3. initializes Git and creates/uses a **private** GitHub repo named `pangram-humanization-lab` through the authenticated `gh` CLI;
4. copies the old autopilot's working lessons/controlled-test ledger when available;
5. imports reusable Pangram 4 results from prior harnesses/calibration folders;
6. prints the cache summary;
7. starts the adaptive experiment.

No Pangram experiment begins until the initial GitHub backup succeeds. After that, each Codex artifact, task-id checkpoint, Pangram result, repeat, statistics file, and analysis artifact is committed and pushed. If GitHub becomes unavailable, the local file is saved first and the run stops before another paid detector submission.

## What you see while it runs

Codex output is streamed as it happens:

```text
[codex:designer] START ...
[codex:designer] ...tool/status output...
[codex:designer] … still working (30s)
[codex:designer] DONE ...
```

Pangram is similarly explicit:

```text
[pangram] CACHE HIT ...
[pangram] RESUME pending task ...; NO new POST
[pangram] SUBMIT new task ...
[pangram] CHECKPOINTED task_id=... before polling
[pangram] SAVED ...
```

## Duplicate-call defense

Base results are keyed by Pangram model + expected API result version + exact submitted-text SHA-256. Exact repeats use deterministic measurement identities. A completed matching record is reused. A pending task is polled using its saved task ID. An ambiguous POST transport failure is **not** automatically resubmitted.

The importer reads the earlier `campaign-state.json`/raw-response form and the newer failed harness's `state.json` form. Pangram 3 results are retained as historical evidence but never substituted for Pangram 4 calls.

## GitHub

The repository is private by default. The installer uses your current `gh` account; it never hardcodes a GitHub username. API credentials are never written to the repository. `.env`, key/secret files, and `.venv` are ignored.

## Experimental contract

The Human endpoint remains editorial authority. Synthetic probes must preserve meaning. The blind reviewer runs before any new Pangram measurements. The planner uses explicit factor assignments rather than brittle `factor_bits`, and contrasts may reference only literal probe IDs; factorial effects/interactions are computed by deterministic code.

## Current external async transport note

Target-machine evidence on 2026-08-12 corrected one part of the Aug. 11 transport assumption. Authentication remains `x-api-key`, and the zero-task `GET /task/<nonexistent UUID>` probe remains non-billable. But a live async submission without a model selector returned terminal version `3.3.2`. The previously validated Pangram-4 harness explicitly requested `model: pangram-4` and returned terminal version `4.0`, so v2.0.1 restores that request field while retaining the newer authentication header.

If an old v2.0 pending task resolves as `3.3.2`, the complete terminal response is archived and pushed to GitHub before one corrected `pangram-4` submission is made. New pending records remember `submitted_model`; if an explicit `pangram-4` request itself ever returns another version, the harness fails closed and will not automatically buy another call.
