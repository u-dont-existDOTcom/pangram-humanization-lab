# Pangram 4.1 GUI readout / credit preflight incident — 2026-10-20

Status: **UNRESOLVED PROVIDER-RESULT/INTERFACE FAILURE**, not a Pangram verdict and not proof of a Pangram 4.1 change in detector internals. A related production owner rule was changed this turn without running any extra tests to validate the rule.

## Scope and verified observations

- Purpose: one first-attempt measurement of an unapproved 54-word Intentional Communities rewrite paragraph about a paid sitter with a feather. Original source and proposed revised copy live in Joel Articles, candidate review folder dated 2026-10-20.
- Target exact text SHA-256: `8caa352b1fdb9361ca377ebde4bc21530a0611c486f9dfb26d00e9ea982e8d7f`; **one** potentially billable submission, no successful result parsed.
- Authorized machine: user's connected HP ProBook; existing dedicated authenticated Pangram GUI Playwright profile. Read-only auth verification succeeded; no input was submitted by that status check.
- First run through old checkout failed **before submission** because local/remote Git histories diverged; no Pangram spend. Isolated safe new worktree `chat/pangram41-community-20261020` created from the remote accepted GUI-runner branch without altering the diverged worktree. Fresh-worktree preflight pushed durable state and wrote a reservation before action.
- Dedicated local GUI runner reported `[pangram-local] submitted sha=8caa...` and then failed to observe the expected report marker within 90 seconds. Failure timestamp in durable evidence: `2026-10-20T16:21:10.567730Z`; stage `wait_report`. The existing parser waits for legacy strings `Authorship Breakdown`, `Analyzed Text` or `of this text is AI/human`. Pangram's GUI 4.1 may have changed the report DOM; equally, a provider/account error may have prevented result creation. **Root cause not established.**
- The full state under the new runner worktree's `state/gui-runs/pangram-4/8caa352b.../` contains `reservation.json` and `failure.json` with `detector_submission_attempted: true`, pushed durably by the runner to its named GitHub evidence branch.
- An attempted `pangram-local recover --input ... --headless` entered an operator-select-History prompt. It could not resolve the exact report without selecting a matching History record. This was interrupted and recorded as readout failure; **no second paid submit**.
- Subsequent read-only authenticated GUI navigation showed the current dashboard's History link and a History view without the candidate phrase in visible text. The authenticated History page displayed **"Credits 0 left"**. This is a UI indicator at the moment of observation, not a verified statement of total account billing or whether this single submission consumed any credit.

## Mandatory next action and non-actions

1. **Do not resubmit** the target SHA through GUI/API or another chat. First recover exact paid request status, completed result and cost from authenticated Pangram History/provider accounting. Treat the one submission as possibly charged until resolved.
2. Update the supported read-only account/credit preflight to check current GUI affordances for an explicit zero-credit state *before* any click; avoid parsing textual errors as success. Never publish auth profiles, cookies or keys.
3. Independently adapt the result-ready predicate and exact-reader-visible-text binding for current Pangram GUI 4.1 using **non-billable** stored History/DOM fixtures; test the error state and the new sentence-level shading legend separately from API Pangram-4 backend version.
4. Do not run other paragraphs, larger context windows, or the full article until result recovery, available credit and the owner production-call budget have been reconciled. The existing draft is unapproved and its predicted Human classification is **not scored** while the actual result is unavailable.
5. Capture the source-to-context shading transition only on real contiguous article sections, not screenshot concatenations from different source locations. All preexisting production stop ceilings remain active.

Disposition: **provisional, GUI/runtime-specific incident**. Promote only after a demonstrably tested non-billable fixture repair and provider-result reconciliation; do not claim all GUI 4.1 submissions are broken from this one incident.
