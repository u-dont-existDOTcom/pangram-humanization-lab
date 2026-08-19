# Pangram local Playwright current state — 2026-08-19

## Goal

Use a dedicated headed persistent local Playwright profile on Joel's Zorin machine as a fully functional Pangram GUI transport while preserving exact-hash identity, ambiguity/duplicate protection, paid-call accounting, recovery-before-repeat, bounded browser tabs, and GitHub durability.

The Pangram API is now independently available through Joel's private self-hosted executor. Continue GUI development anyway: the API and GUI are separate transports, and GUI capability remains useful for report inspection, recovery, visual evidence, and resilience.

## Authority / branch

- Repository: `u-dont-existDOTcom/pangram-humanization-lab`.
- Implementation branch: `agent/pangram-local-playwright-gpt-20260818` / draft PR #78.
- Romance source remains incubator branch `agent/romance-primal-crucible-gui-repair-20260817`; this tooling work does not establish article authority or edit prose.
- Repository visibility is public; normal code-only CI may be used. Detector execution remains intentional and separately gated.

## Independent API transport — live

Owner update, 2026-08-19: Pangram API execution is now available through Joel's own machine/self-hosted execution path. `u-dont-existDOTcom/pangram-private-executor` is the private trusted envelope; it routes approved fixed-batch work to the repository-level self-hosted `pangram` runner and reuses the public lab's canonical cache, pending-task checkpointing, ambiguity guard, call ledger, section cap, result schema, and Git synchronization.

A live private-executor smoke has produced a durable Pangram 4.0 `STAGE_SUCCESS` result on `automation/pangram-fixed-batch`. This confirms API transport availability. It does **not** clear or replace the separate GUI Part-1 ambiguity record.

## Exact current Romance boundary

- Reader-visible total: 20,496 words; SHA-256 `10359ab2119ffbe9a8a7a4a52cd0c3216bb1a6a2c0bffbd7e66fca01287f17ce`.
- Part 1: 10,236 words; SHA-256 `ae88df0f4156537239cb984337196703b88629c3588a5e58ee50c0888d3b39f8`.
- Part 2: 10,260 words; SHA-256 `2df878093bc05fefa98ca30e9a97bdd52e212370f432bf0408e90f1b60c54bb0`.
- Source commit last verified on owner machine: `8e0d70d0ea51fbcb12e307ed0629ed75ee35ce8c`.

## Live local transport already verified

- Brave `/opt/brave.com/brave/brave`, Playwright 1.62.0, Chromium sandbox enabled.
- Dedicated persistent profile `~/.config/pangram-local-browser/`; ordinary Brave profile is never used.
- Manual login completed and fresh-process authentication persistence verified.
- Exact source materialization/hash/word-count gates verified.
- Persistent tab accumulation repaired: normal runs are bounded to one working tab and leave an inert tab on shutdown.
- Self-updating operator wrapper re-execs exactly once if `git pull` changes the wrapper itself.

## Paid-call state — blocking

Audit: `romance-current-20496-pangram-gui-20260818`.

### Part 1 — one paid GUI call, ambiguous, DO NOT REPEAT

- section `romance-current-part-1`;
- paid GUI calls: 1;
- estimated credits/cost: 11 / USD 0.55;
- exact SHA `ae88df0f4156537239cb984337196703b88629c3588a5e58ee50c0888d3b39f8`.

The call reached Pangram. The original capture remained on the initiating dashboard instead of a result bound to the exact submitted document. `failure.json` records `detector_submission_attempted: true`; the durable GUI call reservation remains. No automatic Part-1 GUI resubmission is permitted.

### Part 2 — never submitted through GUI

Part 2 remains uncached on the GUI transport with no GUI paid reservation. It must not run through GUI until Part 1 is recovered exactly.

## Recovery evidence

Prior no-repeat recovery routes established:

1. restored-tab recovery did not find the exact report;
2. older History/scans/reports UI selectors did not find it;
3. Chromium global History is not authoritative for Pangram's SPA record history;
4. All Checks/View Results navigation reached real stored records but the legacy DOM parser rejected current long-document reports;
5. exact `web.pangram.com/api/history/<uuid>/` record matching reached ten stored report candidates but found no byte-identical copy of the authorized Part-1 text.

### Latest owner-machine run — 2026-08-19 06:33 UTC

- deterministic suite: **190/190 passed**;
- browser history/result candidates: **10**;
- exact history API record found: **false** under the then-current byte-exact matcher;
- Part 1 detector submission during recovery: **false**;
- Part 2 GUI submission: **not attempted**;
- recovery stopped fail-closed with the original Part-1 ambiguity intact.

This latest run proves the remaining failure is representation binding, not authentication, browser launch, test health, or accidental repeat submission.

## Current long-document transport evidence

A prior privacy-bounded diagnostic exposed the current long-document contract:

- report page: `https://www.pangram.com/history/<uuid>`;
- report data: `https://web.pangram.com/api/history/<uuid>/`;
- list data: `https://web.pangram.com/api/history-list/`;
- stored record fields include `prompt`, `response`, `response_payload`, `prediction`, `prediction_prob`, `model_id`, and `uuid`;
- current long-document report overview exposes document-level controls such as `AI 8%`, `Human 92%`, and paginated highlight navigation, rather than historical per-segment word-count headings.

The observed 92/8 report remains only a historical candidate until its stored representation is cryptographically/structurally bound to Part 1. Do not assign that score to Part 1 by inference.

## Current representation-binding repair

Detailed checkpoint: `state/PANGRAM-LOCAL-HISTORY-API-EXACT-BINDING-2026-08-19.md`.

The prior exact-record implementation required a literal byte-identical string in the stored JSON. The 190-test live run falsified that as sufficient for recovery. The branch now adds a strictly bounded transport-normalization ladder:

1. exact UTF-8 equality;
2. CRLF/CR → LF line-ending normalization;
3. terminal-newline normalization;
4. outer-whitespace normalization.

Every accepted mode must preserve the complete interior text and identical word count. The receipt records both authorized and stored SHA-256 values plus the explicit `transport_match_mode`. Interior whitespace collapse is **not** accepted as identity.

If none of those modes matches, recovery now emits a privacy-safe comparison diagnostic containing only field paths, character/word counts and deltas, accepted-mode status, substring booleans, and whether whitespace-collapsed equality would hold diagnostically. It never prints stored record text, UUIDs, cookies, storage values, or private result URLs. Whitespace-collapsed equality cannot clear ambiguity.

## GUI completion contract

- `scripts/pangram_local_romance_recover_part1_api.py` remains read-only and has no detector-action path.
- `scripts/pangram_local_romance_paid_api.py` attaches its stored-record response listener before a GUI paid click, preserves the durable call reservation before that click, and accepts completion only after the newly stored record is bound to the submitted text under the same bounded transport contract.
- Human/AI fractions come from the exact bound report's rendered overview; `prediction_prob` semantics are not guessed and synthetic legacy segment counts are not invented.

The operator wrapper routes Part 1 through no-submit recovery and only after a complete cached Part-1 receipt routes Part 2 through the API-record-bound GUI paid runner.

## Next validation/action

1. Run exact-head public CI for the bounded representation matcher and privacy-safe diagnostic.
2. After green CI, run `scripts/pangram_local_romance_recover_resume_safe.sh` on the owner machine.
3. If Part 1 matches under one of the explicitly recorded transport modes, persist/cache it and permit only the uncached Part 2 GUI call.
4. If no bounded match exists, stop and use the new comparison diagnostic to characterize the storage transformation before broadening any identity rule.

## Stop conditions

Stop before resubmitting Part 1 through GUI, bypassing its reservation/ambiguity block, submitting Part 2 through GUI before exact/bounded Part-1 recovery, using Joel's ordinary browser profile/history, committing browser/session/auth/API-record content, guessing score semantics from `prediction_prob`, accepting collapsed interior whitespace as identity without a separately proven transport contract, inventing legacy segment counts, accepting a generic report marker, or rewriting Romance prose merely to simplify detector transport.
