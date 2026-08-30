# Somatic R15 exact Pangram recovery

Status: **ACTIVE / EXACT GUI RESULT COMPLETE / SUPERVISOR DECISION REQUIRED BEFORE EDITING**

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
