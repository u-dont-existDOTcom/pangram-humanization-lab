# Somatic r15 remaining natural sections — 2026-08-28

Status: **FROZEN / PRESERVATION-PASSED / EIGHT PAID API CALLS AUTHORIZED / NOT YET DISPATCHED**

Authority: detector evidence for non-authoritative production candidates only. The registered Somatic master remains `articles/somatic-therapies/master.html` at SHA-256 `1e7e94717f40e7a4de77974a896f600a1bf2769d9c1846cbe84275e136ff5202` and is not changed.

Source article checkpoint: `u-dont-existDOTcom/joel-articles@agent/somatic-humanization-r02-preservation-20260824`, commit `5b6eccc4cea11c7367f5372710026b0ad2ee59a9`.

## Decision this batch can change

The r15 whole-article boundary is AI/high, while several owner-specific anchors and repaired local boundaries are already Human. This batch measures the eight remaining natural section boundaries once so the next production assembly can freeze Human sections and limit source recovery or minimum-dose repair to sections whose result changes the editorial decision.

The fixed batch contains exactly one call each for Somatic Experiencing, trauma-sensitive yoga, gentle shaking/TRE, Brainspotting, EMDR, Light CBT/narrative integration, outcome checking, and Sky Hypnosis/Vagal Blitz. It uses stable section ids under the existing `somatic-r15-section-localization-20260827` audit.

## Exact identity

Fixed spec: `experiments/somatic-r15-remaining-natural-sections-api-20260828-a.json`

Spec SHA-256: `7098b8d4047299b1e350b9b35a5cb3d6d0a72f2609a66653c56f90a059ea6e4f`

| Variant | Section id | Exact text SHA-256 | Words |
|---|---|---|---:|
| `R15_SE_R01` | `somatic-experiencing` | `98feb44a2caf72aed740e1ea5bd00423eda0a2b5fa01a52eb46e4be4d34d4426` | 123 |
| `R15_YOGA_R01` | `trauma-sensitive-yoga` | `a9d23a0b9dd9873b54b57dc01dfcaf7420ed942f848b5bf76aca75e3a0d57bf5` | 149 |
| `R15_GENTLE_SHAKING_R01` | `gentle-shaking-tre` | `47aac9bcc50eaecc16dced6f1761d21f4d0c306dc3f2d9e23c46dac24ef2737b` | 110 |
| `R15_BRAINSPOTTING_R01` | `brainspotting` | `c56a69962b6948a5dbc417ea038ca7e78307d532d453eef5ca9f28c63e96ede1` | 392 |
| `R15_EMDR_R01` | `emdr` | `fcca0b74d933aa5a0272e74ec3feb9b9b8ef6936e019bb591db237b6b2c5c3a5` | 234 |
| `R15_LIGHT_CBT_R01` | `light-cbt-narrative-integration` | `144dab2fc78f6ff3128c20fdd2503cff8212cb4f799b7f9a5280eb22a0c447a0` | 138 |
| `R15_OUTCOME_R01` | `outcome-checking` | `15671184858926e261b24ef3ff38f35ecef07d939e00eda595e729699ba68b99` | 448 |
| `R15_SKY_VAGAL_R01` | `sky-hypnosis-vagal-blitz` | `6709b565113070f6c8e0a4d4a2ef60b1c12160fb8b5a9025fc2377ed8f78e48a` | 210 |

The exact inputs are the eight files under `inputs/`. Their hashes include the terminal newline and match the fixed spec texts exactly.

## Preservation and exclusions

All claims, examples, safety rules, evidence qualifications, links, and owner-specific distinctions within the eight scopes are preserved. Light CBT adds only the routed borrowed-adulthood function; Sky/Vagal adds only the routed deep-work readiness rule. Unexplained substantive deltas: **0**.

Known-Human EFT/head-massage and Louka/Shaking Qigong anchors are excluded. The historical exact Shaking Qigong r01 API reservation remains ambiguous and blocked from repetition. The completed `Where I Would Start`, reparenting R08–R11, and all other completed or ambiguous exact hashes are also blocked from this batch.

## Dispatch rules

1. Dispatch only the immutable spec SHA above through the private fixed-batch executor.
2. Require durable pre-call reservation and exact `audit_id` + `section_id` cap checks before each paid request.
3. Do not use `--force`, change variant order, or create a replacement request while the immutable request is queued or running.
4. Persist each task/result before advancing to the next variant.
5. Stop automatically if duplicate/cache/history or reservation ambiguity appears.
6. A Human result freezes the exact section. AI/Mixed localizes a repair boundary but never authorizes changing protected owner prose merely because it lies in a red window.

Maximum new paid calls: **8**. Untouched-Human controls: **0**. Repeats: **0**.
