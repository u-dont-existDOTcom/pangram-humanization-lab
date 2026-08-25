# Pangram local GUI — Somatic r15 recovery and exact result

Date: 2026-08-25

## Outcome

The local headed Playwright/Brave transport completed a Pangram 4.0 GUI scan of the exact Somatic r15 reader-visible plaintext and persisted an exact stored-History-bound result without using the private API or GitHub executor.

Exact reader-visible boundary:

- source repository: `u-dont-existDOTcom/joel-articles`;
- source branch: `agent/somatic-humanization-r02-preservation-20260824`;
- source commit: `debe32a6fa4f2be1be0435538184a2b7c98af003`;
- source path: `articles/somatic-therapies/experiments/R15-PANGRAM-LOCALIZED-REWRITE-CANDIDATE-20260825.md`;
- source-file SHA-256: `e7a541e75cf06878c206bcd7d78440bb73593a0a5a2169df1446ce42ad7186ee`;
- visible-plaintext SHA-256: `d5101f998fcd6b04b022b50dab49a616d538de8c69c15f286bc1cdc009ecae7e`;
- 3,548 whitespace words / 21,090 UTF-8 bytes;
- materialization began at the unique `# Introduction` boundary, retained visible headings/list text, removed Markdown syntax and all 16 link destinations, excluded seven native/editor placeholder lines, and excluded eight non-prose thematic dividers.

Exact Pangram result:

- Pangram 4.0 / `STAGE_SUCCESS`;
- headline `AI Detected` / prediction short `AI`;
- AI `0.8451970816`;
- AI-assisted `0.0`;
- Human `0.1548029035`;
- stored `prompt` exact-matched the authorized UTF-8 bytes and 3,548-word boundary;
- transport match mode `exact_utf8`;
- exact History record appeared 12.989 seconds after the durable local reservation;
- result commit `d9462f2e93a808c2da4195352e0a7b9a016c94b7`;
- result path `state/gui-runs/pangram-4/d5101f998fcd6b04b022b50dab49a616d538de8c69c15f286bc1cdc009ecae7e/result.json`.

This is a measured diagnostic result, not a 100% Human pass and not owner acceptance of r15.

## Original Git failure and reversible reconciliation

The initial generic GUI invocation stopped before browser work because `durability.preflight()` tried to push local `HEAD` `22b7c44250dfd3eccf42fca22e94c3fed04d190a` while the real hosted task branch was at `7ee60cb1b9e49444debc1d732440554142a332cc`.

The local `origin/...` label had been stale. A live fetch established that the hosted tip was a strict four-commit descendant and changed only `state/` paths. Before reconciliation, rollback branch `recovery/pangram-before-remote-ff-20260825` was created at `22b7c44`. The checkout then fast-forwarded cleanly to `7ee60cb`.

The pre-existing dirty bytes were preserved:

- `src/pangram_humanization_lab.egg-info/SOURCES.txt` remained SHA-256 `0d3e273e20065d756c474c602c07ee94728672396a4cae18d03ea86778af232c`;
- the unrelated untracked `Qwen3.8-27B-Uncensored-MLX/` directory remained untouched.

## Durable tooling repairs

Commit `73c8b2936548f249a1d5ea280ee67482c3b88768` repairs ordinary remote-only durability advances:

- fetch and inspect the matching hosted branch before push;
- automatically fast-forward only a strict remote descendant whose changed paths are entirely below `state/`;
- refuse runtime-affecting remote changes until an operator update/restart;
- refuse true two-sided divergence without automatic merge, rebase, reset, or force-push;
- preserve dirty working-tree bytes through Git's normal fast-forward safety checks.

The first post-repair submission used the previously preserved raw-Markdown `/tmp` bytes. Pangram accepted the click, but the legacy generic parser could not parse the current document-level report. That ambiguity was committed at `19ff8ca45c3bee71818148a5f38bc2bf14092eec`; it was not retried. Commit `88a59e2d85d833c586ec327e906c2b88e59859a5` added a no-submit exact-History recovery path. The accepted record was recovered exactly at result commit `fd288c05bc0611fd27fe79538884be0ecf7a71af`.

That raw-Markdown boundary included source markup and native-object placeholders, so it remains diagnostic-only under the repository's reader-visible boundary rule:

- SHA-256 `6b9c090a2faf10e472f73b747a916cec1169b60d27564de2558628c04a0cb48d`;
- Pangram 4.0 / `STAGE_SUCCESS`;
- AI `0.8463050723`, AI-assisted `0.0`, Human `0.1536949277`;
- no repeat submission occurred; the existing exact History record was recovered read-only.

Commit `2298450815726fe693ddc8362ba8c0ded32ce721` then hardened new generic GUI runs:

- write and push a per-input reservation before the detector click;
- block an unresolved reservation after an unclean stop;
- prefer exact stored-History identity and structured `response.overall` fractions over the obsolete segmented parser;
- retain the legacy segmented parser only as a compatibility fallback;
- mask private History identifiers in committed receipts.

The final deterministic gate after all repairs was **208 passed**.

## Paid-call accounting

Audit: `somatic-r15-whole-article-gui-20260825`

Section: `whole-article-reader-visible`
Ledger: `state/pangram-call-ledgers/somatic-r15-whole-article-gui-20260825.json`

- paid GUI calls: 2 / cap 6;
- call 1: raw-Markdown diagnostic accepted once, then recovered without repeat;
- call 2: corrected reader-visible plaintext completed directly through exact History binding;
- estimated credits: 8;
- estimated cost: USD 0.40;
- cache hits: 0;
- pending resumes: 0.

No further Pangram call is required to complete the runner-recovery task.

## Next safe action

Treat the 15.4803% Human result as article-specific localization evidence. Any further r15 prose editing or paid detector iteration belongs to the Somatic editorial/preservation workflow and must preserve the existing whole-article gates and call cap. Do not repeat either exact GUI measurement.
