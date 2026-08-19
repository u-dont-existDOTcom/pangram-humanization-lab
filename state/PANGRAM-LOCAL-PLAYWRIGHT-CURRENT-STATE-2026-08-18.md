# Pangram local Playwright current state — 2026-08-19

## Goal

Use a dedicated headed persistent local Playwright profile on Joel's Zorin machine as the primary Pangram GUI transport while preserving exact-hash identity, ambiguity/duplicate protection, paid-call accounting, recovery-before-repeat, bounded browser tabs, and GitHub durability.

## Authority / branch

- Repository: `u-dont-existDOTcom/pangram-humanization-lab`.
- Implementation branch: `agent/pangram-local-playwright-gpt-20260818` / draft PR #78.
- Romance source remains incubator branch `agent/romance-primal-crucible-gui-repair-20260817`; this tooling work does not establish article authority or edit prose.
- Repository visibility is now public; normal code-only CI may be used. Detector execution remains intentional and separately gated.

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

### Part 1 — one paid call, ambiguous, DO NOT REPEAT

- section `romance-current-part-1`;
- paid calls: 1;
- estimated credits/cost: 11 / USD 0.55;
- exact SHA `ae88df0f4156537239cb984337196703b88629c3588a5e58ee50c0888d3b39f8`.

The call reached Pangram. The original runner captured the initiating dashboard instead of a result bound to the exact submitted document. `failure.json` records `detector_submission_attempted: true`; the durable call reservation remains. No automatic Part-1 resubmission is permitted.

### Part 2 — never submitted

Part 2 remains uncached with no paid reservation. It must not run until Part 1 is recovered exactly.

## Recovery evidence

Prior no-repeat recovery routes established:

1. restored-tab recovery did not find the exact report;
2. older History/scans/reports UI selectors did not find it;
3. Chromium global History is not authoritative for Pangram's SPA record history;
4. All Checks/View Results navigation reached real stored records but the legacy DOM parser still rejected current long-document reports.

The latest owner-machine run passed **181/181** deterministic tests, made **no repeat Part-1 detector submission**, and made **no Part-2 detector submission**.

Its privacy-bounded structural diagnostic exposed the current long-document contract:

- report page: `https://www.pangram.com/history/<uuid>`;
- report data: `https://web.pangram.com/api/history/<uuid>/`;
- list data: `https://web.pangram.com/api/history-list/`;
- stored record fields include `prompt`, `response`, `response_payload`, `prediction`, `prediction_prob`, `model_id`, and `uuid`;
- current long-document report overview exposes document-level controls such as `AI 8%`, `Human 92%`, and paginated highlight navigation, rather than the historical per-segment word-count headings.

The 92/8 report observed in the diagnostic is only a historical candidate until the stored API record itself exact-matches Part 1. Do not assign that score to Part 1 by inference.

## Current exact-record repair

Detailed checkpoint: `state/PANGRAM-LOCAL-HISTORY-API-EXACT-BINDING-2026-08-19.md`.

The branch now uses exact stored-record identity:

- `src/pangram_lab/history_api_record.py` accepts only `web.pangram.com/api/history/<uuid>/` records whose in-memory JSON contains the literal submitted text;
- exact proof records the authorized UTF-8 SHA-256, word count, and JSON field path without committing the raw API record;
- `scripts/pangram_local_romance_recover_part1_api.py` revisits existing stored reports read-only and can clear Part-1 ambiguity only after exact stored-text identity; it contains no detector-action path;
- `scripts/pangram_local_romance_paid_api.py` attaches the exact-history listener before a paid detector click, preserving the durable call reservation before the click and accepting completion only after the newly stored record exact-matches the submitted text;
- current Human/AI fractions are parsed from the exact report's rendered overview; the runner does not infer `prediction_prob` semantics or invent segment word counts.

The operator wrapper routes Part 1 through the no-submit API recovery, and only after a complete cached Part-1 receipt routes Part 2 through the API-bound paid runner.

## Validation status

The public repository's workflow-policy check is green on the exact-record work. The first full-suite CI attempt reached **189 passing tests** and failed only because a new test helper mistakenly tried to Python-compile the Bash wrapper. That test-harness defect has been corrected. Final exact-head public CI must be green before the next owner-machine run is authorized.

## Next safe action after green CI

Run `scripts/pangram_local_romance_recover_resume_safe.sh`.

The wrapper must:

1. self-update/re-exec if needed;
2. run the complete local deterministic suite;
3. recover the already-paid Part 1 through exact stored history-API identity without submitting it again;
4. persist/cache the exact recovered Part-1 result;
5. only then permit the uncached/unambiguous Part 2 call;
6. bind Part 2 to its own exact stored history record before accepting completion;
7. stop as ambiguous after any paid click whose exact stored record cannot be bound.

## Stop conditions

Stop before resubmitting Part 1, bypassing its reservation/ambiguity block, submitting Part 2 before exact Part-1 recovery, using Joel's ordinary browser profile/history, committing browser/session/auth/API-record content, guessing score semantics from `prediction_prob`, inventing legacy segment counts, accepting a generic report marker, or rewriting Romance prose merely to simplify detector transport.
