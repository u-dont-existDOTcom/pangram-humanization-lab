# Somatic R15 exact Pangram recovery

Status: **ACTIVE / FINAL REPAIR CANDIDATE EXACT GUI RESULT COMPLETE / SUPERVISOR DECISION NEXT**

Task: `somatic-r15-clean-continuation-20260830`

Article repository branch: `task/somatic-r15-clean-continuation-20260830`

Detector repository branch: `task/somatic-r15-exact-recovery-20260830`

## Frozen authority

- source repository: `u-dont-existDOTcom/joel-articles`;
- immutable R15 candidate Git blob: `e6210eb2742de156f0bd7b01fdde269f9b9625c6`;
- immutable R15 candidate SHA-256: `e7a541e75cf06878c206bcd7d78440bb73593a0a5a2169df1446ce42ad7186ee`;
- current deterministic boundary SHA-256: `9a81bd04252a2ee851dd111040c600837bdf0a7bbf71c42c293e3b763c99a707`;
- current boundary size: 3,548 whitespace words / 21,087 UTF-8 bytes.

The current boundary is derived directly from the immutable R15 candidate. Historical R16 is not an R15 identity oracle; it is evidence only for the general visible-text extraction convention.

## Historical exact-candidate evidence requiring reconciliation

Immutable detector commit `d9462f2e93a808c2da4195352e0a7b9a016c94b7` records one Pangram 4.0 GUI result whose source metadata binds to the same R15 candidate path, source commit, and source-file SHA-256. Its stored History prompt was exact-bound at SHA-256 `d5101f998fcd6b04b022b50dab49a616d538de8c69c15f286bc1cdc009ecae7e`, 3,548 words / 21,090 UTF-8 bytes.

That historical detector input is three bytes longer than the current boundary. Authenticated recovery found its exact stored prompt and proved the difference: the historical input retained the four source-only Markdown italics markers around `subcortical` and `restimulation`, while the current reader-visible boundary removes those four markers and preserves one additional terminal newline. Reconstructing those exact five operations from the current boundary reproduces historical SHA-256 `d5101f…`, 20,992 characters, and 21,090 UTF-8 bytes exactly.

The historical result is therefore valid near-boundary evidence for the same immutable R15 candidate, but it is not an exact result for current boundary `9a81bd…`. Interior non-whitespace Markdown markers are outside every accepted transport normalization, so the historical result cannot be reused as an exact cache hit.

## Pre-submission classification

Persisted classification after cache, reservation, authenticated GUI History, browser recovery, and GitHub evidence reconciliation:

**`EXACT_R15_NEVER_SUBMITTED`**

The exact basis is recorded in `state/recovery/somatic-r15-clean-continuation-20260830/detector-state.json`. The article cold preflight passed, the authenticated read-only status check remained clear, and the runner pushed a fresh exact pre-click reservation before the one authorized submission.

## First verified runtime check

The deterministic `pangram-local status --headless --check-auth` command verified the dedicated Brave profile as authenticated without filling or submitting text. The current `9a81bd…` content-addressed directory had no result and no ambiguous reservation in this clean task branch. That local absence is not a final cross-branch or History classification.

## Completed recovery evidence

- standard deterministic History recovery inspected the current ten application-History candidates and wrote `state/gui-runs/pangram-4/9a81bd04252a2ee851dd111040c600837bdf0a7bbf71c42c293e3b763c99a707/failure.json`; no exact record was found and no submission occurred;
- the dedicated-profile recovery surface contained 55 Pangram report routes; the bounded probe inspected 36 authenticated records before finding historical `d5101f…` and found no current `9a81bd…` record;
- the recovered `d5101f…` detector fractions and History identity reproduce immutable Git result commit `d9462f2e93a808c2da4195352e0a7b9a016c94b7`;
- exact-hash Git searches across local refs found `9a81bd…` only in this recovery work and the article recovery branch;
- an organization GitHub issue/PR/code search found only article recovery PR #73 and no detector result, reservation, or other historical occurrence for `9a81bd…`;
- no exact cache result, pending task, GUI reservation, ambiguous click record, History record, browser-recovery record, or GitHub detector evidence exists for `9a81bd…`.

Related paid history remains counted: the historical audit records one raw-Markdown diagnostic call and one `d5101f…` near-boundary GUI call. Changing to the corrected reader-visible boundary does not erase either call.

## Exact GUI result

Current classification: **`EXACT_R15_RESULT_EXISTS`**

The deterministic local runner submitted the exact `9a81bd…` boundary once through the authenticated Pangram GUI after pushing reservation commit `73d60339`. Result commit `134f5191a8142cf91427d22098439763ba276597` records exact UTF-8 History binding to the submitted text:

- Pangram 4.0 / `STAGE_SUCCESS`;
- headline: `AI Detected`;
- Human: `0.1547368467`;
- AI: `0.8452631831`;
- AI-assisted: `0.0`;
- exact stored text SHA-256: `9a81bd04252a2ee851dd111040c600837bdf0a7bbf71c42c293e3b763c99a707`;
- exact stored word count: `3548`.

Result evidence is at `state/gui-runs/pangram-4/9a81bd04252a2ee851dd111040c600837bdf0a7bbf71c42c293e3b763c99a707/result.json`. The related paid-call ledger now counts three calls total: the two historical related calls plus this one exact reader-visible measurement. No further paid call is authorized.

## Localization recovery

The first read-only History localization recovered all nine contiguous window metadata records and six exact substring bindings without submission. The observed window coordinate space is 20,900 characters; the exact 20,989-character text maps to it deterministically by collapsing each contiguous linebreak run to one linebreak and trimming the terminal linebreak run. A tested fail-closed binder now supports that observed transform only when the full collection is contiguous and every stored preview matches its normalized coordinate.

Before that improved binder could be rerun against the live record, the Pangram History route stopped returning the exact record in a new browser session. Two recovery-only retries failed at `bind_exact_history_record`; both durably record that no detector submission was attempted. The original complete result remains cached and authoritative for the document score. The privacy-safe diagnostic window map at `state/recovery/somatic-r15-clean-continuation-20260830/exact-result-window-map.json` therefore distinguishes durable Pangram window metadata and exact-text offset reconstruction from independent score authority.

Per the task protocol, the next action is a matching result packet to the existing Chat supervisor. A red window is not edit authority, and no detector-driven prose edit begins before that decision.

## Final repair-candidate recovery

Supervisor decision `SOMATIC-R15-REPAIR-004` authorized one later whole-document Pangram 4 GUI measurement only after the bounded micro-repair passed its gates and blind verification and exact recovery proved the final boundary had never been submitted. Those prerequisites now pass.

The final non-authoritative repair candidate is blob `082b613f5d5217ebb8b289ee0460a788a66e2639` / SHA-256 `7600316ff4895f694e430b317a750a80c4ed2848b474bf475757ae3c6f0e26b6`. Its deterministic reader-visible boundary is blob `31cabafedfe2433dd6fa8fd1badc31f31491bc28` / SHA-256 `129fee7e8ab844fcd65db38807841c51db9883d85ed5079c93323a01cf640f9e`, 3,585 whitespace words, 21,260 Unicode characters and 21,356 UTF-8 bytes.

Persisted pre-submission classification: **`EXACT_FINAL_NEVER_SUBMITTED`**.

Evidence:

- read-only authenticated status verified the dedicated Brave profile and exact hash gate; no text was filled or submitted;
- no exact cache result, ambiguous reservation or completed reservation exists;
- standard authenticated History recovery inspected the ten server-side list candidates and found no exact match;
- the task-scoped full-profile probe inspected all 60 retained Pangram report routes and all 60 authenticated History API records, finding no exact match;
- exact local-ref, organization GitHub code, and organization issue/PR searches found no prior occurrence before this receipt;
- recovery attempted no detector submission.

The new measurement is decision-relevant because the candidate changed semantically within four supervisor-authorized repair scopes and then passed source, preservation, architecture, cold-audit and independent-reader gates. Related paid history remains three calls before this action, below the six-call ledger cap. The next action is the deterministic runner's durable pushed reservation followed by one GUI click. If the click may occur and later capture fails, recovery—not retry—is mandatory.

## Final repair-candidate exact result

Current classification: **`EXACT_FINAL_RESULT_EXISTS`**.

The deterministic runner pushed reservation commit `0b20ac9dabb14d0b0c6cc12d6d7ffcf47fc99b9f` before its only click. Result commit `ab98314386b6d289a8425aff857b8b15eb663ee5` records exact UTF-8 History binding:

- Pangram 4.0 / `STAGE_SUCCESS`;
- headline: `AI Detected`;
- Human: `0.1381948739`;
- AI: `0.861805141`;
- AI-assisted: `0.0`;
- exact stored text SHA-256: `129fee7e8ab844fcd65db38807841c51db9883d85ed5079c93323a01cf640f9e`;
- exact stored word count: `3585`.

The completed History report displayed three `AI Highlight` regions and the summary `AI-generated content appears throughout`. Read-only DOM inspection exact-mapped them to: boundary start through the end of EFT; the middle of Shaking beginning `I did not try the linked class…` through the end of Light CBT / Narrative Integration; and `I care more about the hour-later version…` through the final coda. Exact offsets and span hashes are in `final-candidate-display-highlight-map.json`.

Two post-result structured-localization attempts failed closed at exact History rebinding and made no detector submission. The exact aggregate result remains authoritative; the display map is localization evidence only. Related paid history now totals four calls under the six-call cap, and no further measurement is authorized.

The score and broad highlight topology do not establish a new writing defect. The supervisor-authorized repair passed independent editorial gates and a detector-blind bounded verification, while Pangram's Human fraction decreased from the exact original R15 result (`0.1547368467`) to `0.1381948739`. This is negative evidence against another detector-led rewrite. The required next action is `WORKER_SUPERVISION_REQUEST SOMATIC-R15-POSTREPAIR-005`, recommending `READY_FOR_OWNER_REVIEW` without changing registered article authority.
