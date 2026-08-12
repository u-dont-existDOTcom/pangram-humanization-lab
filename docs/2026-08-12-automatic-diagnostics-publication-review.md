# Automatic Diagnostics Publication Verification Review

## Scope

This review covers runtime `1.3.0-dev1` on source commit `34fa011f9d6435954985e02f634b8c383c5f5034`. The change is operational only. `project/` and `policy/` are byte-identical to the verified `1.2.0-dev1` baseline commit `825db90de18aa74ba1ebe5cc035771d24adc3a09`.

## Root cause and implemented boundary

Earlier releases created complete local evidence packages but never transported a result beyond Joel's Zorin machine. Version 1.3 adds a strict allowlisted diagnostic record, atomic local outbox, disposable Git checkout, and nonblocking publication call at installer and runtime return/restart boundaries. Normal publication targets the separate orphan branch `diagnostics/authorial-flow-graph-v1` in `u-dont-existDOTcom/pangram-humanization-lab`. A transport failure leaves the runtime result unchanged and retains the record for retry.

The remote record excludes article/source/candidate/rejected prose, prompts, transcripts, stdout/stderr bodies, exception messages, credentials, environment values, full local paths, and evidence ZIP bytes. Unknown free-form values are hashed and labeled `UNCLASSIFIED` rather than copied.

## Deterministic verification

- Full suite: `352 passed in 8.60s` with Pangram, Brave, OpenAI, and Anthropic environment keys removed from the test process.
- Diagnostics CLI/transport integration: a real local bare Git repository received `LATEST.json` and the append-only dated run record through the `publish-results` command boundary.
- The real-Git tests cover orphan-branch creation, source HEAD/status invariance, sequential and duplicate publication, queue recovery after remote failure, canonical-remote selection, and non-fast-forward retry without force-push.
- Release build: `verification=PASS`; graph `1.3.0-dev1`; policy `joel-articles-4.12.0-candidate`; project-instructions count `3175` characters; clean-extraction compilation passed.
- Protected-tree comparison: `git diff --quiet 825db90..34fa011 -- project policy` returned zero.
- Captured incident compatibility: 29 checkpoint history records opened under 1.3; copied SQLite SHA-256 remained `b88267c0e5611e0e9a7b6ca586f366af3d9e9cba9ba23e7e7a88c90decf297cc` before and after the read.

## Target-machine boundary

The deterministic tests do not prove that Joel's existing Git credentials can push the canonical private repository from Zorin. The installer or next runtime outcome must create/update the remote diagnostics branch. If it reports `AUTH_REQUIRED`, `NETWORK_UNAVAILABLE`, or another typed failure, the record remains under `.state/diagnostics/outbox/`; `./RUN.sh publish-results` retries it without uploading the full evidence package.

## Locale-stability correction

The first target-machine retry selected the canonical remote but returned `diagnostics_status=queued`, `failure=GIT_FAILURE`, `attempts=1`, and `queued=2` while the remote diagnostics branch did not exist. Review of the failing boundary found that first-publication detection and typed Git failure classification depended on English stderr tokens even though the target is French Zorin. A regression reproduced the defect with a real child process: under inherited French `LC_ALL`, a localized missing-ref message raised `CalledProcessError` instead of selecting the orphan-branch path.

Patch commit `0687a0c5b0aa59a315445ffeb411b240c4db7db0` normalizes only the diagnostics Git child's message locale. It removes child `LC_ALL` after preserving its effective value as `LC_CTYPE`, then sets `LC_MESSAGES=C` and `LANGUAGE=C`. The parent Python process, UTF-8 path handling, credential-helper environment, queued records, diagnostic schema, and privacy boundary are unchanged.

An attempted shell probe with global `LC_ALL=C` did not reach Authorial Flow: Python selected an ASCII filesystem encoding and failed on the `Téléchargements` path, and the prompt showed that the command was launched from another project. No Authorial Flow queued record was removed or published by that attempt. The corrected target probe changes only message translation: `LC_MESSAGES=C LANGUAGE=C ./RUN.sh publish-results` from the Authorial Flow directory.

- Regression RED: localized missing-ref handling failed with `CalledProcessError` before the patch.
- Regression GREEN: `1 passed in 0.03s` after the patch.
- Focused diagnostics/privacy suite: `20 passed in 0.66s`.
- Full suite: `353 passed in 9.76s`.
- Clean release build: `verification=PASS`; graph `1.3.0-dev1`; policy `joel-articles-4.12.0-candidate`; project-instructions count `3175`; release SHA-256 `0ed2a7e9acfe4472293aab7447cbeabf04eb9675cf5da6dee7a8268112f31ce0`.
- Protected-tree comparison: `git diff --quiet cc910f5..0687a0c -- project policy` returned zero.
- Remote check at `2026-08-12T18:41:30Z`: `diagnostics/authorial-flow-graph-v1` was still absent, so live target publication remained pending and the two local records remained the authoritative evidence queue.

## Root release-metadata correction

The 1.3 source tree still carried the 1.2 root `MANIFEST.json` and `SHA256SUMS.txt`. The ZIP builder was not producing stale metadata: it deliberately excluded those root files and generated correct replacements inside every ZIP. The release CLI simply had no operation to install those generated bytes back at the root, and the release tests inspected only ZIP-internal metadata. The manual 1.2 finalization step was therefore omitted from 1.3 without a failing gate.

Tooling commit `b930c31b6445ca7819bae1fd9cb545f1cd00b45a` adds an executable `--write-root-metadata` operation and defines metadata-only Git commits as excluded release bookkeeping. The source-commit resolver walks backward across commits that change only root `MANIFEST.json` and `SHA256SUMS.txt`, so a clean rebuild from the final metadata commit remains byte-identical and identifies the preceding content-bearing commit. A synthetic regression exercises the real CLI under a `Téléchargements` path, commits only the synchronized metadata, rebuilds, and compares both embedded files byte-for-byte.

- Root-metadata regression RED: the CLI rejected the missing `--write-root-metadata` operation because `--out` was mandatory.
- Root-metadata regression GREEN: `1 passed in 0.11s`.
- Complete release suite: `22 passed in 4.19s`.
- Pre-finalization full suite: `354 passed in 10.57s`.
- Pre-finalization clean release build: `verification=PASS`; graph `1.3.0-dev1`; policy `joel-articles-4.12.0-candidate`; project-instructions count `3175`; SHA-256 `b4a6907cd277b8d9d4338a44c024cc02b4a52bc21286a7d0cdc0b5bf9acea962`.
- Protected-tree comparison against `cc910f53525d2af7a24175bc28c4282d17732c14`: zero differences under `project/` and `policy/`.
