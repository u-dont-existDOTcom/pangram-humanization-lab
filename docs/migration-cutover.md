# Migration and Cutover — Legacy Supervisor to Authorial Flow Graph v1

## Production boundary

The legacy supervisor, nested harness, and autopilot packages are read-only historical evidence. They are not invoked by the new runtime and are not dependencies of the release.

The production path is:

`INSTALL-AND-RUN.sh` → `authorial-flow` CLI → LangGraph graph → typed nodes/adapters/checkpointer → owner interrupt only when authorial information is genuinely missing.

Interactive supervision is part of that same path, not a second runtime. Ctrl+C asks the active graph to checkpoint and route to `supervisor_pause`; confirmed actions resume the existing thread through LangGraph's normal `Command(resume=...)` boundary.

## What was migrated

The legacy free-will experiment remains development evidence, including owner-labeled bad transitions, semantic-relation regressions, Pangram baseline metadata, source/context fixtures, and known orchestration failure cases. Those records constrain evaluation and testing without making the inherited Claude paragraph semantic authority.

## What was retired

- nested supervisor → autopilot → harness orchestration;
- hand-carried intermediate ZIPs and logs;
- source-order positive transitions as hard authority;
- mandatory coverage of AI-derived semantic atoms;
- post-hoc model self-certification as a substitute for owner judgment;
- detector-first acceptance.

## Cutover gate

Legacy orchestration is considered retired from active development only after the exact release ZIP demonstrates on the target machine:

1. dependency installation under `~/Téléchargements`;
2. Claude and Codex capability checks;
3. LangGraph checkpoint interruption/resume;
4. hard owner/semantic regressions;
5. Pangram downstream behavior and task resume;
6. a genuine owner interrupt and resume without script/version transfer.

Until then, the legacy artifacts remain evidence only; they are never reintroduced into the live path as a fallback runtime.

## In-place checkpoint compatibility

Version 1.1 added optional state fields for supervisor snapshots/sessions, owner directions, rejected proposals, per-move coverage, and pause metadata. Version 1.2 adds optional boundary IDs, safe decision traces, provider failure kinds/capability signatures, and bounded repair history/outcomes. Version 1.3 adds only `.state/diagnostics/` outbox/status files and a separate remote diagnostics branch. Existing SQLite checkpoints remain valid because every graph-state field added in earlier versions is optional and 1.3 does not alter the checkpoint schema. There is no destructive database migration, checkpoint rewrite, or `.state` reset.

An installed project resumes from `.state/current-thread.json` and therefore preserves its stored thread ID. The release-baseline reconciler may update the local source commit while retaining `.state`; it must never reseed an interrupted article. A legacy checkpoint without per-move coverage may continue normally, but rollback fails closed until bounded two-call coverage reconciliation validates the exact move hashes and authority-unit mapping.

Legacy pressure and edge results without a 1.2 boundary ID remain historical observations only; the generation node recomputes pressure for the current accepted boundary before using it. A legacy repair history begins empty. The first 1.2 repair attempt records a signature and typed outcome, after which an unchanged duplicate stops before review. Upgrading does not replay or mutate accepted prose merely to populate these optional fields.
