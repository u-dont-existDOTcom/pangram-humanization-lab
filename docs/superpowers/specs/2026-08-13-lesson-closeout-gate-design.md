# Lesson Closeout Gate Design

## Goal

Make lesson capture a completion invariant rather than a memory-dependent editorial habit.

## Architecture

A machine-readable ledger binds semantic finding dispositions to exact source-artifact SHA-256 values. A stdlib-only CLI records dispositions, audits current refs, and checks changed ranges. GitHub Actions enforces changed-range closeout on pushes/PRs and runs a weekly orphan audit that opens/updates one issue when unresolved research exists.

## Semantics

Allowed dispositions: `promoted`, `provisional` (`experimental` input alias), `article-specific`, `superseded`, `no-new-lesson`.

Every post-enforcement tracked research artifact must have at least one ledger entry for its current exact hash. Non-promoted findings require a reason. Promoted findings must target the canonical `state/LESSON-INDEX.md` plus a `state/WORKING-LESSONS*.md` summary, and those targets must change in the same checked range.

## Scope

Tracked by default: Romance/Pangram/historical research notes under `state/`, experiment JSON under `state/experiments/`, and reconstruction notes under `notes/`. Existing pre-gate artifacts are grandfathered by last-modified timestamp; modifying one after enforcement requires fresh closeout.

Long-lived branch evidence may be dispositioned into the main ledger with `--source-ref`. Weekly audit covers `main` and `automation/pangram-fixed-batch`.

## Safety

The gate never promotes a detector finding automatically. It only requires an explicit semantic disposition. Raw detector evidence remains distinct from durable editorial lessons. Pangram status never controls promotion by itself.
