# GPT-only prose transfer: preregistered A/B/C and adaptive two-stage D/E

Date: 2026-10-24. Status: **exploratory experiment completed; positive detector signal in one rhetorical job; generator skill NOT yet transferred**. This is a research record, not a new owner-approved article master and not model-weight fine-tuning.

## Objective and isolation

Objective: improve GPT prose generation *without using Emulate at inference time*, while preserving every substantive authorial point, and decide whether the problem is inherited source syntax or composing the thought.

**No Emulate requests were made in this entire study.** The C condition saw two historical, meaning-audited, Pangram-Human positive pairs (one Emulate-informed, one owner-endorsed); D/E saw neither pair nor Emulate material. Fresh authenticated GPT-6.1 Sol **High** Codex CLI contexts were used: **6 preregistered isolated writers, 2 isolated semantic planners, 4 isolated adaptive writers**. Each `--ephemeral --ignore-rules -C /tmp -s read-only` writer received only its exact frozen prompt; six initial and four adaptive logs showed no unexpected tool-call lines. This is *writer-level context isolation*, not proof of complete environmental isolation or fresh evaluation of targets to the supervising model.

Two holdout passages from an existing indexed owner-calibration corpus: **H-SOM** (somatic trauma / gradual engagement, model-shaped controlled reverse pair) and **H-CHICKEN** (inner-child adult-role chicken-and-egg, historically owner-rewritten). The holdout owner references were not supplied to any writer or blind reader.

Preregistration and source data: `fixtures-and-prereg.json`, `prompts-frozen.json`. Exactly frozen AI outputs: `results-raw-frozen.json`. Fresh separate Claude Opus blind editorial judgments: `blind-review-frozen.json`, with arms concealed at review time. The labels, gold reference and objective were reconciled only after results were frozen.

## Stage 1: single-pass prompt treatments A/B/C — NEGATIVE

- **A:** conventional faithful rewrite.
- **B:** same task with concise causal/situation planning instructions.
- **C:** B with two literal positive before→after demonstrations (a preserved-role Inner Child paragraph and Joel-endorsed forgiveness revision).

On both holdout tasks, the blind editorial reader independently ranked **A > C > B** for publication fitness. On H-SOM A/C both had fidelity PASS and naturalness **4/5** (A more faithful/clean); B had naturalness **3/5** and some misplaced timing emphasis despite PASS. On H-CHICKEN A/C passed fidelity, while B was UNCERTAIN due invented vague question, extra “still” and heavier rhetorical restaging. The blind reader's naturalness evaluation is not an author detector or a substitute for Joel's reading.

**Predeclared matched Pangram 4.1 comparison, H-SOM A vs C:** identical source, fresh isolated outputs and valid exact History binding. Both **100% AI** by `response.overall.fraction_ai=1.0`; A confidence Medium (AI boundary), C confidence High. This test **does not support a claim that positive examples alone, or more prescriptive planning rules, teach this GPT to generate Human prose**. A's higher blind editorial rank did not prevent a Pangram AI result.

Raw proofs: `pangram-pair-exact-readout.json`; `pangram-pair-preflight.md` freezes prediction and budget.

## Stage 2: adaptive different architecture (D/E) — MIXED

After the Stage 1 negative result, preregistered a **separate two-stage writer**: a fresh model receives a meaning card and produces a short causal/attention plan without any publication sentences; the next fresh writer composes prose from that plan and a sanitized card.

Within each target, the identical cleaned plan and card went to two arms:
- **D:** no original AI-shaped source sentences.
- **E:** the same card/plan plus the original source sentences for fidelity only.

Before writer calls, the H-SOM planner prepended an irrelevant UTC/bootstrap line, stripped mechanically. The H-CHICKEN planner and card introduced an unsupported reassurance about *insincerity*, also stripped before both D/E writers. The amendment and corrected cards/plan hashes were committed before any D/E generation. This exposed a **planning-stage source-fidelity risk** distinct from sentence rhythm.

Four GPT outputs were frozen in `adaptive-results-raw-frozen.json`; the two blind reviews were frozen in `adaptive-blind-review-frozen.json`.

**H-CHICKEN:** both D and E **FAIL** independent preservation review. Both soften the original strong experience into abstract uncertainty, substitute “inherited critic” for “old critic,” and change the rhetorical job. **No Pangram calls** on those meaning-failed outputs.

**H-SOM:** both pass the independent meaning check. Blind reader: D 4/5 naturalness, not publication-ready (the final “Knowing what's needed ... separate things” is an excessive abstract recap; “around the edges” repeated). E 3/5 naturalness but preferred for publication because it retained the detailed causal claim without D's categorical closing aftercare. These are model-critic ratings only, not Joel's reading test.

**Matched Pangram 4.1 on H-SOM D/E, exact History bound:**

| Condition | Detector Human | Detector AI | Mixed / AI-assisted | Headline | Confidence |
|---|---:|---:|---:|---|---|
| D: source hidden, card + plan | **97.2929%** | 1.0730% | 1.6341% | Mostly Human Written | Low |
| E: source visible, SAME card + plan | **99.9062%** | 0.0937% | 0.000047% | Human Written | Low |

Both GUI short-text outputs are labeled “Possibly human” and should not be called *High confidence*. The authoritative values were read from exactly matched `response.overall` in stored Pangram 4.1 History, without resubmission; `adaptive-pangram-pair-exact-readout.json` contains the SHA, bound word counts, timestamp proximity, version and fractions with no private History URL.

**Causal interpretation:** the adaptive two-stage composition architecture produced strongly Human-classified GPT prose on one holdout where single-pass A/C scored 100% AI. This is a **promising first-pass transfer signal**, not proof of a generalizable skill. Because D and E *both* classified Human, merely *hiding the original source sentences* was **not necessary** for that success. Multiple factors also changed between Stage 1 and Stage 2 (a separate semantic planner, card wording, time/length and output architecture); the difference cannot be causally assigned to any one of them. H-CHICKEN's simultaneous meaning failure prevents promoting the method.

## What to carry forward — and what not to claim

1. **Do not treat detector PASS as good prose.** Joel's own reading test was not performed on these exact D/E drafts; the fresh blind editor still found staged staccato, repeated phrases, abstract closing commentary or expository density.
2. **Do not assume a larger anti-pattern rulebook teaches generation.** The A/B/C comparison showed no improvement from causal instructions or two literal successful demonstrations.
3. **A separate meaning/causal-planning component is promising**, but can generate its own unsupported assumptions (the *insincerity* contamination); before any writer composes, a distinct source-fidelity validator must check the plan against frozen original claims and protect attribution, certainty, action and reader intent. Remediation must not become another paragraph of safety disclaimers.
4. **Keep writer and reviewer informationally separated.** A same-context “ignore the model answers” writer would not be blind. Freeze exact prompts, model, outputs, pretest diagnoses and detector receipts.
5. **Only call this OBSERVED/EXPLAINED + one promising detector transfer on H-SOM**, **NOT TRANSFERRED_TWICE / PRODUCTION_SKILL**. A fresh owner-graded rhetorical job is required.

### Next independent test that would matter

Select a new, genuinely unseen Joel-byline paragraph from current Git authority (different rhetorical function than somatic explanation and child-state advice). Freeze source/preservation units. Run a **source-faithfulness gate on the *planner card*** before exposing either card or prose to the new writer; reject assumptions and rationalizations at that stage. One fresh GPT writer then composes from a validated card plus plan, without Emulate or source-sentence imitation. Separately cold-review meaning/prosody, get Joel's own reading judgment **without revealing Pangram outcome**, and only then buy a single exact-context Pangram 4.1 check if the candidate deserves it. Compare with a simultaneously frozen same-target baseline; require two distinct owner-approved transfers before promotion.

No article master, writer rule, or protected owner correction has been changed or promoted from this research. The parent objective remains improving generator skill without Emulate; the current evidence is incomplete.
