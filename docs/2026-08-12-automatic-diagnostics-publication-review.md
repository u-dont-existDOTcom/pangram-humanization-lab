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
