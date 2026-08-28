# Pangram Humanization Lab current state

Updated: 2026-08-28

## Goal

Preserve exact Pangram detector evidence, editorial authority, lesson closeout, and paid-call safety while keeping the owner's transport choice explicit. **When Joel asks for a Pangram GUI check, use the local headed Playwright/Brave transport on his Zorin machine as the primary route. Do not silently substitute the private API/executor route.**

Current owner instructions, exact repository evidence, tests, and current `main` outrank historical chat or old task branches.

## Current browser-interaction preference — 2026-08-28

For multi-candidate Pangram work, Joel asked that Brave remain in the background and that the automation reuse its existing session/tab instead of repeatedly foregrounding, closing, and reopening tabs. The completed Human→AI packet used headless Brave with one persistent context and one reused result tab per batch. Treat this as the current interaction preference unless Joel asks to watch a headed run. It does not relax authentication, exact-identity, reservation, cache, or History recovery safeguards.

## Current completed Human→AI packet — 2026-08-28

`state/experiments/human-to-ai-minimal-pairs-20260828/` contains the frozen design, exact candidates, 15 Pangram-4 results, preservation receipts, call accounting, and durable lessons. Untouched Human baselines were not resubmitted and no completed exact candidate was repeated. The production-level lesson is stacked editorial closure and feature interaction, not phrase banning. R09's owner result is now recorded as paragraph 1 Human/high and paragraph 2 AI/high. This research does not change article authority.

## Owner transport correction — 2026-08-25

Joel directly corrected the routing drift that had made later workers treat GitHub/private-executor Pangram as the only practical path. The earlier working GUI workflow remains the intended workflow for explicit GUI checks:

`local execution / Codex supervision -> deterministic pangram-local runner -> headed local Brave via Playwright -> pangram.com`

Operational consequences:

- `GUI check`, `check it in Pangram GUI`, or equivalent language means **local Playwright GUI**, not Pangram API.
- Use the dedicated persistent browser profile `~/.config/pangram-local-browser/`; do not use Joel's ordinary Brave profile.
- The validated browser executable is `/opt/brave.com/brave/brave`.
- The local transport is headed by default so Joel can see the browser work.
- The persistent Pangram login is local browser state. Never commit cookies, storage, credentials, or profile contents.
- GitHub may be used for code/versioning and durable receipts after or around a run, but **GitHub is not the GUI transport and must not be treated as a prerequisite for the browser interaction itself**.
- Do not claim that the GUI route is unavailable merely because a particular Chat context lacks a local command/computer-use bridge. Recover the local runner state first. If execution cannot be launched from that context, say exactly that rather than rerouting to the API by inference.
- Do not make Codex or another agent free-form click around when deterministic Playwright can perform the bounded browser actions.
- Preserve cache/ambiguity/no-repeat protections across transports.

The local GUI route was live-certified end-to-end on Joel's Zorin machine on 2026-08-20 for long Pangram documents, with headed Brave, persistent authentication, exact stored-text binding, History recovery, result parsing, duplicate-call defense, and PDF capture.

## Authority and recovery

- Canonical repository branch: `main`.
- Long-lived fixed-batch/evidence branch: `automation/pangram-fixed-batch`.
- Private trusted execution envelope: `u-dont-existDOTcom/pangram-private-executor`.
- Self-hosted runner labels: `[self-hosted, linux, x64, pangram]`.
- Start lesson recovery at `state/LESSON-INDEX.md`.
- Start repository documentation at `docs/INDEX.md`.
- Self-host/API correction evidence: `state/PANGRAM-SELFHOST-ROUTING-CORRECTION-2026-08-20.md`.
- Local GUI documentation: `docs/PANGRAM-LOCAL-PLAYWRIGHT.md`.
- Historical local GUI validation/evidence: `agent/pangram-local-playwright-gpt-20260818` and its durable state.
- Historical Romance GUI/evidence branches remain provenance only and do not establish article authority.

## Current transport architecture

### Local Playwright GUI — primary route when Joel asks for GUI

The reusable local authenticated-browser transport is the owner-preferred route for an explicit Pangram GUI check, visual report inspection, History recovery/localization, and browser evidence.

It uses:

- a dedicated persistent automation profile, not the owner's ordinary browser profile;
- headed Brave/Chromium through Playwright;
- exact input SHA-256 and optional pre-authorized hash gates;
- a durable submission reservation before a detector click when the guarded runner is used;
- authenticated History observation and exact stored-text binding;
- explicit Pangram 4 `response.overall` structured fractions;
- recovery-before-repeat after ambiguous action;
- bounded tab cleanup and privacy-limited diagnostics.

The generic command is `pangram-local`. The historical validated command surface is:

```text
pangram-local bootstrap
pangram-local verify
pangram-local run --input FILE [--input FILE ...]
pangram-local recover --input FILE
pangram-local status
```

The previously validated local installation was under `/mnt/hdd/home/joel/Téléchargements/pangram-local-runner-20260818/` with its own `.venv`. See `docs/PANGRAM-LOCAL-PLAYWRIGHT.md` and `state/PANGRAM-LOCAL-PLAYWRIGHT-CURRENT-STATE-2026-08-18.md` on the historical implementation branch for exact recovery details.

### Private self-hosted Pangram executor — programmatic API route when API is intended

For ordinary **API/programmatic** Pangram measurements where Joel has not asked for GUI evidence, the private executor remains a supported trusted route.

The execution contract is:

1. freeze the exact public-safe fixed-batch spec on `automation/pangram-fixed-batch`;
2. verify its exact SHA-256;
3. add exactly one immutable `requests/<request-id>.json` to `u-dont-existDOTcom/pangram-private-executor`;
4. the private workflow validates the request/spec and dispatches the canonical public runner to `[self-hosted, linux, x64, pangram]`;
5. cache, task checkpointing, explicit Pangram-4/version gates, call ledgers, result persistence, and ambiguity protection remain in the public lab branch.

The Pangram API key stays in the private executor's trusted environment and must never be retrieved, printed, committed, or requested from Joel.

A fresh uncached route test on 2026-08-20 (`pangram4-selfhost-route-retest-2026-08-20-a`) completed successfully through this exact path:

- Pangram `4.0` / `STAGE_SUCCESS`;
- 60-word fresh input;
- `paid_api_calls: 1`;
- `cache_hits: 0`;
- estimated 1 credit / `$0.05`;
- full detector `windows` metadata returned.

This proves the API route is operational; it does **not** supersede an explicit owner request for the GUI route.

### Single-file API contract

`pangram-lab detect-file` remains the canonical hash-gated/cache-safe single-file API command where an appropriate trusted runtime already has the working Pangram route. See `docs/PANGRAM-API-DETECT-FILE.md`.

Do not infer global Pangram availability or credit state from a different runtime's endpoint result when another transport has fresher direct evidence.

### Browserbase — not an ordinary Pangram route

Browserbase is not the normal measurement route. A Browserbase `HTTP 402 Payment Required` means Browserbase browser-minute quota exhaustion and says nothing about Pangram account credits. Do not buy/retry Browserbase minutes as a Pangram-credit workaround.

Older Browserbase code remains compatibility/history only.

### GitHub-hosted Actions — do not use as the normal Pangram API origin

A known origin-specific compatibility issue (#95) causes GitHub-hosted runners calling Pangram's async external endpoint to return HTTP 401 even when the same credentials work elsewhere. Do not re-debug the API key or route ordinary measurements through GitHub-hosted Actions.

The `automation/pangram-fixed-batch` branch remains the canonical fixed-batch evidence/accounting implementation used by the private self-hosted executor; its historical GitHub-hosted paid workflow must not be confused with the current trusted execution origin.

## Error-source classification

Classify failures by the transport that actually produced them:

- **local Playwright launch/auth/UI failure** -> local GUI/browser issue; do not infer Pangram API/key failure.
- **Browserbase HTTP 402** -> Browserbase minutes exhausted; no Pangram-credit conclusion.
- **GitHub-hosted async HTTP 401** -> known origin-specific compatibility problem; no Pangram-key conclusion.
- **self-hosted Pangram API HTTP 402** -> the Pangram balance available to the trusted self-hosted route is insufficient for that request at that time.
- **repository section-call cap** -> internal safety/cost budget, not Pangram account balance.

A self-hosted 402 for a large request after a smaller successful request supports `insufficient remaining balance for the larger request`; it does not by itself prove a literal zero-credit balance and says nothing about whether the logged-in GUI route can be inspected.

## Current Romance detector evidence relevant to routing

The historical local-GUI certification on 2026-08-20 remains valid evidence for the registered Romance boundary:

### Registered Part 1

- SHA-256 `ae88df0f4156537239cb984337196703b88629c3588a5e58ee50c0888d3b39f8`
- 10,236 words
- Pangram 4.0 / `STAGE_SUCCESS`
- Human `0.9205247164`
- AI `0.0794752836`
- AI-assisted `0.0`
- exact stored-text binding

### Registered Part 2

- SHA-256 `2df878093bc05fefa98ca30e9a97bdd52e212370f432bf0408e90f1b60c54bb0`
- 10,260 words
- Pangram 4.0 / `STAGE_SUCCESS`
- Human `0.8983033895`
- AI `0.1016966403`
- AI-assisted `0.0`
- exact stored-text binding

These two historical half measurements are not a measured whole-article score and do not establish article authority.

The active 2026-08-20 Romance detector-repair audit subsequently produced stronger candidate evidence on task/evidence branches. Its best completed Part-2 result at that checkpoint was pass 3, SHA `c6ef42419a3db2e82b1ff4f9370fc85bca4fa8c061c61dd6a1b5d28171d9908c`, Human `0.9153165817`.

Pass 4 was frozen at SHA `a21b9670bc0cc61b4fc850761ca57ffa5dc5d1a02bdd5df90b820d6f9d437a0e`, 9,985 words. The trusted private self-hosted executor reserved its fourth Part-2 audit slot and Pangram returned HTTP 402 `Insufficient credits` before issuing a task ID. That API event must not be generalized into `Pangram GUI unavailable`.

## Paid-call safety

The six-new-paid-calls per stable audit/section cap remains binding unless current owner authorization explicitly changes it.

Across transport changes, preserve one stable audit/section identity and import already-paid measurements into the current call ledger rather than resetting the budget. Before any new paid action:

- check exact cache/completed results;
- resume a checkpointed task/report rather than resubmitting;
- treat ambiguous POSTs or GUI clicks as potentially paid;
- never repeat a completed exact measurement;
- for API calls use explicit `model: pangram-4` and require returned `version: "4.0"`;
- for GUI calls bind completion to the exact stored History prompt/result where available;
- persist reservation/checkpoint/result/ledger state before another paid request when using the guarded runner;
- keep the reader-visible SHA-256 and word count exact.

Code-only preparation/CI must not spend Pangram credits.

## Mainline GUI promotion history

The reusable local browser/auth/profile/history/result modules were previously promoted onto `main` from a clean then-current base. That promotion passed the full deterministic suite, changed-file lesson closeout, repository audit, and workflow policy without detector submission.

The dedicated local Playwright workflow was then live-certified on Joel's machine with long documents. Do not demote that evidence merely because later API routing was added.

## Current blockers / unresolved

- A given Chat context may or may not expose the local command/computer-use bridge needed to launch Joel's headed Brave session. This is a context capability issue, **not** evidence that the Pangram GUI route itself stopped working.
- The trusted self-hosted Pangram API route was operational at the last direct route test, though a large Romance request later hit an API-side balance 402.
- The pass-3 read-only History localizer had a recovery reliability bug tracked in issue #110; do not buy detector calls solely to debug it.
- Hosted-control hardening remains separate governance work and is not detector/article authority.

## Next safe action

For an explicit **GUI check**:

1. recover/verify the local `pangram-local` installation and dedicated profile first;
2. use headed local Brave/Playwright;
3. verify authentication read-only before filling/submitting;
4. check exact cache/ambiguous state before any new click;
5. capture the exact report/History identity and result;
6. persist evidence afterward as useful, without treating GitHub as the browser transport.

For an explicit **API/programmatic check**, the private self-hosted executor remains available under its existing safety contract.

Never silently substitute one transport for the other when Joel has specified GUI vs API.

## Recovery rule

After interruption or a fresh chat, inspect this checkpoint, `docs/PANGRAM-LOCAL-PLAYWRIGHT.md`, the historical live-validation state `state/PANGRAM-LOCAL-PLAYWRIGHT-CURRENT-STATE-2026-08-18.md` on `agent/pangram-local-playwright-gpt-20260818`, `state/LESSON-INDEX.md`, and the active article task state. Inspect API/private-executor state only when the requested transport is API or when cross-transport paid-call ambiguity makes it relevant.

Never infer paid-call state from chat. Never repeat ambiguous/already-paid work before exact durable state is recovered or deliberately resolved.

## Completed Somatic reparenting production matrix — 2026-08-28

The exact packet is on branch `experiment/somatic-reparenting-production-matrix-20260828` under `state/experiments/somatic-reparenting-production-matrix-20260828/`. Four authenticated Brave/Pangram UI calls completed with exact staged SHA verification, pre-click GitHub reservations, result-text binding, and four matching History rows. No completed input was repeated; untouched R08 and known R09 were not submitted.

Results: M00 Human/100%/medium; M01 Human/100%/medium; M10 Mixed/displayed 35% AI with a later AI/high A-cluster segment; M11 Mixed/displayed 46% AI with exact R08 Human/high and the complete extension AI/high. The direct UI exposed rounded percentages, so no unavailable unrounded fraction is inferred.

Disposition: the constant concrete Nurturer/Protector/action cluster is Human and the light-hypnosis cluster is Human without A. The neutral-witness/borrowed-adulthood cluster is the decision-relevant conditional trigger in this exact boundary, with hypnosis amplification when A is present. This does not isolate individual phrases. No production-complete Human cell emerged. M01 is frozen only as a detector-Human partial building block; R08 remains frozen; article authority is unchanged.
