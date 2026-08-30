# Somatic R15 exact Pangram recovery

Status: **ACTIVE / READ-ONLY RECOVERY BEFORE ANY SUBMISSION**

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

That historical detector input is three bytes longer than the current boundary and is not yet proven byte-identical to it. The historical result must therefore be recovered and compared at the exact text boundary before classifying the current R15 action state. Do not infer either a cache hit or a never-submitted state from the label `R15` alone.

## Required classification

Persist exactly one only after cache, reservation, authenticated GUI History, browser recovery, and GitHub evidence have been reconciled:

- `EXACT_R15_RESULT_EXISTS`;
- `EXACT_R15_ACTION_AMBIGUOUS`;
- `EXACT_R15_NEVER_SUBMITTED`.

No detector submission is authorized during this recovery phase. A new GUI click becomes eligible only if the article cold preflight passes and exact recovery proves `EXACT_R15_NEVER_SUBMITTED`.

## First verified runtime check

The deterministic `pangram-local status --headless --check-auth` command verified the dedicated Brave profile as authenticated without filling or submitting text. The current `9a81bd…` content-addressed directory had no result and no ambiguous reservation in this clean task branch. That local absence is not a final cross-branch or History classification.
