# Single-file Pangram API route — 2026-08-20

Status: tooling change; **no paid detector call occurred while implementing or testing this code**.

## Problem

Current repository authority correctly routes ordinary programmatic detector work through the owner's working API path, but the CLI exposed only the older adaptive multi-input experiment command. A one-off article boundary therefore required ad hoc Python even though `PangramClient`, `PangramCache`, and `GitSync` already implemented the required cache/checkpoint/no-duplicate safeguards.

## Change

Add `pangram-lab detect-file` for one exact UTF-8 boundary.

The command:

- requires `--expect-sha` and refuses a changed input before credential access;
- uses a stable `--measurement-key` for cache/checkpoint identity;
- accepts `PANGRAM_BASE_URL` / `--base-url` so the owner's current API route can be selected without code edits;
- probes authentication without creating a billable task;
- delegates submission, pending-task resume, ambiguous-submit refusal, Pangram-4/version gating, and result persistence to the existing `PangramClient.detect_cached` implementation;
- Git-syncs preflight state and lets the existing client Git-sync pending and terminal cache records;
- reports exact input SHA, word count, measurement identity, cache path/status, model/version, and result.

## Public-cache safety

The canonical Pangram repository is public and the existing `PangramCache` stores exact detector text. `detect-file` therefore requires explicit `--allow-public-cache`; without it the command stops before credential access. This option is appropriate only when the frozen detector boundary is already public-safe. Private/unpublished text needs a different durable-cache design rather than bypassing the guard.

## Scope

This command does not change the six-paid-call section cap, reader-visible representation gate, article semantic/fidelity gates, or completion target. It is transport/tooling only and creates no new detector-language lesson.

Finding disposition: **no-new-lesson**. The durable reusable change is the command and its safety documentation, not a Pangram prose heuristic.
