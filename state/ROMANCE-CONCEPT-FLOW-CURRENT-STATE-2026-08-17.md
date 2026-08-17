# Romance Concept-Flow Current State — 2026-08-17

## Goal

Improve concept setup, primary explanatory homes, later callbacks, and the specific owner-authorized Romance passages from the Aug. 17 handoff without genericizing Joel's worldview, weakening claims, losing unique material, or allowing detector output to override semantic/editorial authority.

## Authority / baseline

- Working branch: `agent/romance-concept-flow-improvement-20260817`.
- Recovered source head: `agent/romance-architecture-map-2026-08-16@4ac56a883f147a59a003c05c3387423399609f8b`.
- Recovered pre-pass reader-visible boundary: 18,268 words, SHA-256 `25ce4bd4e5845884a5c8988ba88f87e2a5e2f469417402cf1cc9cc8b0594a3d2`.
- `joel-articles/main` remains a governance incubator with no verified canonical Romance article import. Do not publish private Romance prose there merely to satisfy future registry structure.
- Current explicit Joel corrections plus the private assembly/state chain in this repository control this task.

## Completed

### Concept architecture audit

Durable audit: `state/ROMANCE-CONCEPT-SETUP-AUDIT-2026-08-17.md`.

Results:

- card-game intimacy versus lived evidence: added the missing disclosure-created-closeness limitation and kept ordinary-life observation as the evidentiary shift;
- community/shared social reality: added a compact early seed; `Two Pillars Don't Hold The Roof Up` remains the full explanatory home;
- honesty/privacy/timing/material disclosure: **no new generic framework** because the continuous article already establishes the distinction in place;
- readiness: preserved a categorical floor and named both inner-child parenting and literal parental responsibility;
- idealization: linked spiritual/archetypal depth to ordinary dependability without moving the detailed flaws examination;
- Crucible: explicitly separated mutual activation/growth from unilateral terror/control and safety concerns;
- labels/agreements/vows: labels do not create commitment but can reveal mismatched relationship meanings; explicit agreements remain downstream; vows heading now matches the existing conduct-versus-future-feeling argument;
- psychedelics/MDMA: moved the consent/safety warning before attractive altered-state material while preserving state-dependent learning and sober evidence.

### Authorized prose changes

Durable exact old/new ledger: `state/ROMANCE-CONCEPT-FLOW-PROSE-CHANGE-LEDGER-2026-08-17.md`.

Materialized changes include:

1. card-game felt closeness versus lived compatibility;
2. early shared-community reality seed;
3. readiness floor in both senses of parenthood;
4. sourced bundling example as an imperfect historical intermediate courtship form;
5. idealization -> ordinary dependability bridge;
6. Crucible coercion/safety boundary plus repaired post-warning antecedent;
7. labels -> shared meaning correction;
8. Bee door passage explicitly preserving that she lied while adding possible mental-illness context;
9. heading `Which marriage vows are honest?` without rebuilding an argument that already distinguishes feelings from conduct;
10. MDMA warning before positive psychedelic material;
11. later readiness callback changed only enough to say personal standards vary `above that minimum`.

### Bundling source control

Durable note: `state/ROMANCE-BUNDLING-SOURCE-NOTE-2026-08-17.md`.

The article treats bundling as old, mostly extinct, especially associated with Amish courtship but historically broader. It states that bundling coexisted with high premarital pregnancy in late-eighteenth-century New England and does **not** claim bundling caused the pregnancy rate or that contemporary Amish communities generally practice it.

### Cold audits

Durable audit: `state/ROMANCE-CONCEPT-FLOW-COLD-AUDIT-2026-08-17.md`.

Two independent cold-read stages were completed. The first identified and repaired:

- clipped generated reversal cadence in card-game/readiness/MDMA candidate wording;
- overcausal/report-like bundling wording;
- a broken Crucible pronoun antecedent after the new warning;
- a later readiness line that could sound like it weakened the categorical floor.

The second literal whole-master read found no further legitimate editorial weakness inside the authorized scope requiring another prose change.

### Mermaid architecture

`work/romance-current-assembly/ARCHITECTURE.md` is synchronized to the current materialized boundary and now includes focused drill-downs for:

- cards -> testimony -> ordinary-life evidence -> revisit;
- readiness -> intermediate courtship stage -> sex/entanglement;
- idealization -> healthy-adult evidence -> flaws -> Crucible;
- mutual Crucible versus coercion -> safety;
- labels -> shared meaning -> agreements -> vows;
- early community seed -> Two Pillars -> later applications;
- MDMA warning -> altered-state intimacy -> state-dependent learning -> sober evidence.

The map remains a visual control surface, not prose authority.

## Current checkpoint

### Exact materialized article boundary

Materialized article commit: `22b2929885cb55426c2a2b174eb39808c332b008` (`state: materialize current Romance master and visible boundary`).

- Master: `work/romance-current-assembly/current-master.md`
- Source bytes: 109,929
- Source SHA-256: `2d9fdbe0d2406fad2c9778130aeebfeb4a157061fad46597d42817ad876739b1`
- Reader-visible bytes: 107,593
- Reader-visible words: 18,748
- Reader-visible SHA-256: `7a972576aab329e2afa10278b598596e2acfcc4f6d56a8656785a91df6b5213c`
- Assembly operations: 35

The final bundling operation was refactored from a separator-adjacent `replace_between` to one exact atomic replacement so the source replacement file does not need artificial trailing whitespace. This changed assembly bookkeeping only; the final article bytes/hash stayed the same.

### Verification evidence

Green non-paid verification run: GitHub Actions run `31998979512` on head `12673a76256c01f1b4045ead981ea53203080ffc`.

Verified in that run:

- full repository test suite: **104 passed**;
- deterministic reassembly matches committed `current-master.md` exactly;
- assembly manifest matches exactly;
- generated diff body matches after excluding its path-dependent file header;
- reader-visible text matches exactly;
- reader-visible manifest matches after excluding its deliberately path-dependent `source_path` field;
- architecture map indexes exact source SHA, reader-visible SHA, and 18,748-word boundary;
- explicit owner-lock assertions pass, including Bee lying, categorical readiness, MDMA warning order, vows heading, oxytocin, cervical-evidence structure, sexual/social monogamy distinction, and terminal Subscribe marker;
- required concept-audit/state/spec/plan artifacts exist;
- `git diff --check` passes for source/state files; the generated `current-master.diff` artifact is excluded because its literal patch syntax represents added blank lines as `+ ` and is not source prose;
- `python scripts/audit_codex_github.py --root . --fail-on error` passes with **0 errors, 5 warnings**. The warnings are repository-level controls/packaging issues unrelated to this article edit: code scanning disabled, default-branch rules disabled, secret-scanning push protection unverified, secret scanning unverified, and no recognized lockfile;
- `scripts/validate_content_repository.py` and `scripts/validate_article_architecture_maps.py` are not present in this private repository, so they were not falsely reported as run.

## Blockers / unresolved

### Pangram API credential

The repository-secret Pangram route reaches the API but the paid POST currently fails with HTTP 401 `Invalid API key`. Joel has contacted Pangram support about the new key. Do not start duplicate paid API work while that credential issue remains unresolved.

### Detector state

The current 18,748-word reader-visible hash has **not** been Pangram-certified.

Manual Pangram 4.0 PDFs supplied by Joel correspond to the previous 18,248-word split boundary:

- Part 1: 11,506 words; 92.5% Human / 7.5% AI; High-confidence segment localization.
- Part 2: 6,742 words; 98.9% Human / 1.1% AI; High-confidence segment localization.
- Separate Primal diagnostic: 574 words; 54% AI / 46% Human with alternating High-confidence red/green blocks.

These PDFs are useful localization evidence but do not classify the new exact boundary. Joel's Aug. 17 `After leaving` owner rewrite remains editorial authority even though the GUI labels that local text AI/High and `paraphrased or rewritten`.

## Evidence / artifacts

- Specification: `docs/superpowers/specs/2026-08-17-romance-concept-flow-improvement.md`
- Implementation plan: `docs/superpowers/plans/2026-08-17-romance-concept-flow-improvement.md`
- Concept audit: `state/ROMANCE-CONCEPT-SETUP-AUDIT-2026-08-17.md`
- Bundling source note: `state/ROMANCE-BUNDLING-SOURCE-NOTE-2026-08-17.md`
- Prose change ledger: `state/ROMANCE-CONCEPT-FLOW-PROSE-CHANGE-LEDGER-2026-08-17.md`
- Cold audit: `state/ROMANCE-CONCEPT-FLOW-COLD-AUDIT-2026-08-17.md`
- Architecture: `work/romance-current-assembly/ARCHITECTURE.md`
- Assembly spec: `work/romance-current-assembly/assembly-spec.json`
- Materialized master/diff/manifests: `work/romance-current-assembly/`
- Non-paid verification workflow: `.github/workflows/romance-concept-flow-verify.yml`

## Remaining

- Manual Pangram GUI localization on the **current** exact boundary while API access is broken.
- Do not automatically reopen Talk: the prior assistant detector repair became 100% AI/High and no independent semantic defect currently justifies another rewrite.
- Primal remains the clearest detector-localized unresolved region, but any repair still has to pass the article/coherence gate before wording work.
- After the Pangram key is fixed and the prose boundary is stable, register one final exact reader-visible whole-article experiment for the current SHA rather than certifying an obsolete hash.

## Next safe action

Use the manual Pangram GUI on current reader-visible Part 1/Part 2 boundaries, preferably preserving a split comparable to the previous report so the block progression is interpretable. Start with the new current Part 1 because the largest unresolved detector areas (Talk/Primal) and most of the new concept-flow changes are there. Use focused PDFs only to localize a flagged region after the long boundary has been measured. Do not change owner-final prose solely because a detector window is red.