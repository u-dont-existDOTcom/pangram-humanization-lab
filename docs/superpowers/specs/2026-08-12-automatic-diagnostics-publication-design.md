# Automatic Diagnostics Publication Design

**Status:** Approved by Joel's instruction to fix the missing automatic evidence-publication path and his existing choice to push privacy-safe diagnostics to a separate Git branch.

**Baseline:** `1.2.0-dev1` at local source commit `825db90de18aa74ba1ebe5cc035771d24adc3a09`.

**Preservation mode:** P0 for article, project, policy, owner-gold, semantic-gold, and promoted learning material. This change is operational only.

## Reproduced defect

The runtime successfully builds a local evidence ZIP, but every completion path stops at the local pathname. `bootstrap_repair`, `finalize_bounded_failure`, `finalize_if_accepted`, and the CLI have no Git publication call. The installer can therefore pass or fail on Joel's Zorin machine while the connected private GitHub repository remains unchanged and Work cannot inspect the result.

The attached bounded-failure archive also proves why the full ZIP must never be pushed automatically: it contains project source, policy, checkpoint state, and content-addressed model artifacts. Those files are needed for local forensic recovery but exceed the privacy boundary for routine remote diagnostics.

## Required behavior

1. Significant installer and runtime outcomes create a compact `authorial-flow-diagnostic-v1` JSON record.
2. The record is built from an explicit allowlist. It may contain timestamps, program and graph versions, commit/branch identifiers, content hashes, thread hash, command class, result/status enums, failure class/origin, retry and coverage counts, content-free decision trace, and typed provider capability outcomes.
3. The record never contains source, accepted, candidate, or rejected prose; prompts; transcripts; stdout/stderr bodies; exception messages; credentials; environment values; full local paths; or the evidence ZIP.
4. Records publish to the orphan branch `diagnostics/authorial-flow-graph-v1` in the canonical private repository `u-dont-existDOTcom/pangram-humanization-lab`.
5. Publication uses a disposable Git checkout of only the diagnostics branch. It cannot switch, stage, commit, merge, or dirty the installed source branch.
6. Each successful publication adds `runs/YYYY-MM-DD/<run-id>.json` and updates `LATEST.json` in one commit. Replaying an already-published record is idempotent.
7. A missing remote, unavailable network, authentication failure, timeout, or concurrent push never changes the article/runtime outcome. The record remains in `.state/diagnostics/outbox/`, a content-free status is saved, and the next significant outcome retries the queue.
8. Push races retry from the new remote head a bounded number of times. Git credential prompts are disabled so background publication cannot hang the terminal.
9. `./RUN.sh publish-results` creates a current status snapshot and flushes the queue manually, but normal use does not require this command.
10. The installer preflight, live smoke, `run`, `resume`, `answer`, accepted completion, bounded failure, machine-repair restart, and unexpected top-level interruption all reach the same nonblocking publisher.

## Diagnostic schema

Top-level fields:

- `format`, `run_id`, `created_utc`
- `phase`, `outcome`, `command_kind`
- `graph_version`, `program_version`, `source_branch`
- `thread_id`, `source_sha256`
- `failure_class`, `failure_origin_node`, `repair_outcome`
- `counts`: accepted moves, retries, rollbacks, uncovered required units, event count
- `decision_trace`: the existing content-free allowlist only
- `providers`: provider/model/status/failure-kind/capability-signature/attempt count only
- `artifacts`: evidence and package SHA-256 values only
- `privacy`: schema version plus the permanently excluded categories

Unknown free-form values are represented by a hash and an `UNCLASSIFIED` enum; they are never copied verbatim.

## Git transport

The publisher discovers only a remote whose normalized repository identity equals the canonical repository. It honors `AUTHORIAL_DIAGNOSTICS_REMOTE` and `AUTHORIAL_DIAGNOSTICS_BRANCH` only after validating the remote name/ref and repository identity. Tests may inject a local bare remote directly; production auto-discovery never publishes to an arbitrary repository.

For each attempt it initializes a temporary repository under `.state/diagnostics/tmp`, fetches only the remote diagnostics branch when present, applies all queued JSON records, commits with a fixed non-personal identity, and pushes a fast-forward update. The temporary repository is removed regardless of outcome. Source Git status and HEAD are captured in integration tests before and after publication.

## Failure handling

Remote failures are classified without persisting raw Git stderr: `REMOTE_MISSING`, `AUTH_REQUIRED`, `NETWORK_UNAVAILABLE`, `TIMEOUT`, `NON_FAST_FORWARD`, or `GIT_FAILURE`. The status file contains only the class, branch, run ID, queue count, attempt count, and successful commit SHA when available.

The publisher itself never enters autonomous code repair. A remote credential or network problem is operational state, not a reason to spend Codex calls or modify program code.

## Acceptance criteria

1. A real local bare-remote test proves automatic creation of the separate diagnostics branch while the source HEAD/status remain byte-for-byte unchanged.
2. A secret/prose sentinel placed in environment, source, result fields, provider errors, stdout, and stderr is absent from every outbox file, diagnostics commit, status file, and terminal line.
3. Installer pass, credential-required, account-action-required, repair exhaustion, runtime bounded stop, accepted completion, and supervisor pause each publish the correct enum-only summary.
4. Remote failure queues without changing the wrapped command's exit code; a later successful call flushes the queue.
5. Repeated publication is idempotent, and a concurrent-head change is retried without force-pushing.
6. `publish-results` works from the installed wrapper and never packages or uploads the full evidence ZIP.
7. The complete deterministic suite and exact release build pass with article/project/policy hashes unchanged.
