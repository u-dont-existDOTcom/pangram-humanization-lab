# Claude Code CLI tell-ledger calibration and rubric-development checkpoint — 2026-09-24

Status: **BOUNDED METHOD EVIDENCE / NO PANGRAM CALLS / NO PRODUCTION PROMOTION OF V2.1**

## Parent outcome

Reduce the cost and latency of the full post-generation tell-ledger sweep without losing the fail-safe behavior that made Claude Opus 5.5 preferable to GPT on this task.

This work tests the **provider-native Claude Code subscription CLI** separately from the earlier OpenRouter effort ladder. Provider-surface results are not transferred mechanically.

## Frozen benchmark identity

The CLI effort calibration reused the exact frozen six-case benchmark:
- global tell prompt SHA-256: `b2d3de84afe7798b8910b7a22370ad83b3e2afe1a6b62eb98a6b5f67bef09e9f`
- cases SHA-256: `8bb8a3ba99e617de68c2d146efc15a31d929e72a8dda02c91b039c6d7b0ddd2f`
- scored owner/editorial cells: 12

Transport:
- Claude Code CLI;
- first-party `claude.ai` OAuth / subscription authentication;
- model `claude-opus-5-5`;
- fresh non-resumed requests;
- safe/restricted mode;
- strict MCP;
- tools disabled for benchmark calls;
- no session persistence;
- neutral `/tmp` working directory;
- structured JSON output.

## Claude CLI effort results

| CLI effort | Exact | UNCERTAIN | Wrong polarity | Total elapsed | Thinking tokens | Output tokens |
|---|---:|---:|---:|---:|---:|---:|
| medium | 9/12 | 3 | 0 | 158.135 s | 3,930 | 13,269 |
| high run 1 | 10/12 | 2 | 0 | 156.634 s | 5,837 | 13,435 |
| high run 2 | 10/12 | 2 | 0 | 167.788 s | 6,111 | 13,927 |
| xhigh | 10/12 | 2 | 0 | 218.876 s | 11,759 | 20,598 |

High and xhigh had the same aggregate score and the same fail-safe property: **zero wrong-polarity calls** on the frozen twelve cells. High repeated at the same 10/12 aggregate score. The particular uncertain cells were not perfectly stable, so this is not evidence that high is a perfect deterministic judge.

xhigh used about twice the thinking tokens of high and materially more elapsed time without improving the aggregate result.

### Routing implication

For the **Claude Code CLI route**, `high` is now the current **efficiency target for the full-ledger sweep**, not a sole clearing authority. xhigh does not have evidence of enough extra value to justify routine use on this benchmark.

Escalation should be tell-specific:
- if high returns PRESENT: inspect/repair that tell;
- if high returns UNCERTAIN on a decision-changing tell: use a calibrated narrow auditor, direct editorial review, or a higher-effort Opus request if it can change the decision;
- do not spend max merely because it once reached 11/12 on the API benchmark.

The CLI result does **not** establish that every tell is well calibrated. The later T01/T10/T11 holdout below exposed definition/control problems that the original twelve-cell benchmark could not detect.

## First attempt to make the rubric easier: expanded V2

A Claude-high rubric-development pass converted the tell definitions into explicit gates/subtests and sharply restricted legal UNCERTAIN reasons. The design was motivated by:
- repeated uncertainty around short/manual cadence;
- source-ledger dependence in T04;
- mildness being confused with existence in T08;
- known overlap among T02/T09, T03/T11, and T07/T11.

This expanded V2 was then tested at the same Claude CLI high effort on six new T01/T10/T11 controls that were not in the original six-case benchmark.

### V1 versus V2 on the six-case development holdout

Raw key result before control-quality correction:

| Rubric | Exact | Wrong polarity | UNCERTAIN |
|---|---:|---:|---:|
| V1 | 3/6 | 2 | 1 |
| expanded V2 | 3/6 | 3 | 0 |

Latency:
- V1: about 197 s total;
- V2: about 260 s total.

The expanded rubric was therefore **worse as a method candidate**: more tokens/latency, no accuracy gain, and less fail-safe uncertainty.

### Control-quality correction

The T10 negative control was malformed for the intended tell. It had been labeled ABSENT because it was owner-preferred prose, but owner preference/authorship does not establish absence of a tell. Both V1 and V2 independently found permission packaging in it.

That control is now **CONTESTED / excluded from scoring** until a tell-specific owner/editor judgment exists.

On the five valid controls:
- V1: 3/5 exact, 1 wrong polarity, 1 UNCERTAIN;
- V2: 3/5 exact, 2 wrong polarity, 0 UNCERTAIN.

Do not promote expanded V2.

## What the failed holdout taught

### T01

The old definition lets first person escape whenever the author is genuinely talking about their own therapy or relationship. Joel's owner correction is narrower and more useful:

A first-person want/permission can still be fake-personal **inside autobiography** when it merely wraps a general criterion that would be clearer as a direct criterion.

The useful discriminating question is not “is the author really the participant?” It is:
> if the first person is removed and the criterion stated directly, is any author-specific observation, motive, reaction, experience, or authority limitation actually lost?

### T10

A surface negative imperative is not enough. The tell concerns **permission/relief packaging as a reusable counseling shell**.

A valid negative control must pass the permission gate but be logically anchored to a specific earlier claim, fact, mechanism, exception, or step order so that moving it to another problem breaks the logic.

The first T10 negative control did not meet that standard and must not be used as evidence that the rubric missed.

### T11

Expanded V2 made a bad move by treating “names a relation” as enough to make a bridge substantive. Generic connective tissue can explicitly say that X is why Y matters and still exist only to connect document functions.

The stronger test is:
- does the bridge change the subject's **time, case, premise, condition, or causal state** in a way the next sentence needs?
- if deleted, would the following material still follow, losing only an announcement/relevance statement?

A necessary temporal/case transition can look like a bridge and still be ABSENT for T11.

## V2.1 status

Claude proposed a compact V2.1 that keeps V1 as the base and changes only the decision procedure for T01, T10, and T11. The proposal is stored separately as an **experimental prompt**.

V2.1 has **not** received a fresh blind holdout yet.

Do not:
- replace the production prompt with V2.1;
- claim V2.1 improves accuracy;
- use the consumed six cases as validation;
- use the malformed T10 negative control as an ABSENT label.

The next valid test needs genuinely new, tell-specific controls with labels based on the tell itself, not provenance, detector result, or overall owner preference.

## Jev: exact practical value

TypeSafe Jev 1.13 remains useful as **positive triage only**.

On the original 12 owner/editorially grounded cells:
- overall exact: **9/12**;
- known PRESENT defects caught: **6/9** (about 67% recall in this tiny benchmark);
- known ABSENT controls correctly left ABSENT: **3/3**;
- Jev PRESENT calls: **6/6 correct** in this tiny benchmark;
- all three errors were **false ABSENTs**;
- reported cost across six 12-tell cases: about **$0.00073 total**, about **$0.00012 per candidate**;
- typical latency was sub-second to roughly 1.5 s per candidate.

Interpretation:
- Jev PRESENT is a useful cheap alarm. If editorial inspection agrees, repair before spending a slower Opus sweep.
- Jev ABSENT provides no clearing authority. It missed dangerous-adult abrupt complication, RT2 scene-skinned staircase, and RT2 equalized efficiency.
- The observed 6/6 positive precision and 6/9 recall are too small a sample to treat as stable performance estimates.
- Jev can plausibly save **Opus iterations** by catching some already-blocked candidates early; that workflow saving has not yet been measured prospectively.
- Jev does not improve the final clearance decision by itself and cannot override Opus, a calibrated narrow audit, or direct editorial judgment.

## Current method decision

1. Keep the full tell ledger and specialized narrow-audit architecture.
2. Prefer provider-native Claude Code CLI over metered Opus API when authentication/capability/isolation are adequate.
3. Use Claude CLI **high** as the current efficiency target for the global sweep while broader calibration remains incomplete.
4. Keep any PRESENT or UNCERTAIN unresolved until editorially dispositioned.
5. Use Jev optionally before Opus as positive triage; never use Jev ABSENT as clearance.
6. Do not promote expanded V2.
7. Treat compact V2.1 as an experiment awaiting a fresh blind holdout.
8. Keep OpenRouter xhigh as the current API-fallback setting; max remains escalation only.
9. No Pangram calls were made in this work.

## Partial V2.1 transfer test and method switch

A compact V2.1 kept V1 as the base and changed only T01/T10/T11 decision procedures.

Fresh controls:
- T01 PRESENT: `I care less about...` general criterion wrapper.
- T01 ABSENT: `I don't want to call that checking...` source-required provisional authorial judgment.
- T10 PRESENT: `You don't have to keep producing new versions of the same no.` — contemporaneously audited as a model-shaped permission/advice close.
- T10 ABSENT: `You don't have to make vivid pictures appear just because the words aren't there. Quiet can just be quiet.` — locally anchored correction to the specific false inference that absent words create an obligation to visualize.

Consumed T11 regression controls:
- generic document-linkage bridge: PRESENT;
- required Romance temporal/case transition: ABSENT.

Results at Claude CLI high:
- V1 on the four fresh T01/T10 controls: **2/4 exact**, 1 UNCERTAIN, 1 wrong polarity.
- V2.1 on the same four fresh controls: **3/4 exact**, 0 UNCERTAIN, 1 wrong polarity.
- V2.1 on the consumed T11 pair: **2/2 exact**.

V2.1 fixed both T10 fresh controls and preserved the T11 regressions, but it **over-flagged the fresh T01 ABSENT**. The depersonalization rule treated a provisional first-person classification as equivalent to a categorical rule and therefore erased the speech-act/epistemic-force difference.

This crosses the same-method refinement threshold for T01. Do not add another global-rule patch merely to fit it.

## Specialized T01 architecture

The T01 question was moved out of the global rubric into a one-axis audit.

The specialized test explicitly asks whether depersonalization preserves:
- proposition;
- speech act;
- epistemic force;
- practical force.

It marks ABSENT when first person carries genuine author-specific experience/reaction/motive or a situated/provisional judgment whose depersonalization would become more categorical.

Calibration examples in the narrow prompt:
- two PRESENT controls: generic therapy criteria wrapped in `I want...` / `I care less...`;
- two ABSENT controls: actual relational necessity with a stated mechanism; provisional classification `I don't want to call that checking...`.

Fresh held-out controls:
1. PRESENT — `The test I care about is whether I slowly need the helper less...` general helper criterion.
2. ABSENT — owner-cognition-assisted `I don't want the adult to arrive, grab the pencil...` actual self-relating motive/metaphor.

Claude Opus 5.5 CLI high result: **2/2 exact**.

Interpretation:
- this is scoped evidence that a one-axis audit is better than further global-rubric accretion for T01;
- it is not a universal accuracy estimate;
- retain direct editorial authority and expand two-sided controls before claiming broad certification.

## Current architecture after this checkpoint

- optional Jev positive triage;
- Claude Code CLI high global full-ledger sweep using the compact production base;
- specialized/narrow audit for implicated or disputed axes;
- **T01:** narrow specialized auditor now has a 2/2 fresh held-out transfer;
- **T10:** compact decision rule has 2/2 fresh transfer evidence but has not yet been separately validated as a dedicated narrow auditor;
- **T11:** compact decision rule passes the consumed positive/negative regression pair only; fresh tell-specific validation remains missing;
- direct natural-boundary editorial read remains mandatory;
- Pangram stays downstream.

No Pangram calls were made.

## Narrow-auditor strategy switch — 2026-09-24

The global-rubric V2/V2.1 iterations reached the method-switch threshold. A global prompt change that helped one under-calibrated tell could regress another. The next experiment therefore decomposed T01, T10, and T11 into one-axis auditors rather than adding more global rubric machinery.

### Frozen narrow prompts

Before constructing the new holdouts, three narrow prompts were frozen locally:

- T01 narrow SHA-256: `b52a6aba6e36378a15eadf9d503e08e3d950e2281f59a1290e9c1c3b45d3d5a0`
- T10 narrow SHA-256: `207439ffb284b473371deb6f2ff4d04cf5abd2e01cecc85edd396b0c42aa47d5`
- T11 narrow SHA-256: `c7bfdb481e176aa7b854d1b5cd76d2988023cf2e758a1bcf379fff45a992f5ae`

Each auditor asks one observable editorial question and emits one PRESENT / ABSENT / UNCERTAIN result. No global Human/AI judgment is allowed.

### Post-freeze cross-domain holdout

Each narrow auditor was tested on four controls constructed only after its prompt was frozen.

At Claude Opus 5.5 **high**:
- T01: **4/4**
- T10: **4/4**
- T11: **4/4**

At Claude Opus 5.5 **low** on the exact same controls:
- T01: **4/4**
- T10: **4/4**
- T11: **4/4**

The low runs used zero thinking tokens on all twelve cells.

This synthetic/controlled 12/12 result is useful routing evidence, but it is not sufficient calibration authority by itself.

### Hard real-example regression

The same low-effort narrow auditors were then checked against the harder real development examples that motivated the tells.

**T01 low**
- original owner-rejected therapy preference/permission wrapper: correct PRESENT;
- Romance actual desire/disposition: correct ABSENT;
- `I care less about...` fake-personal criterion wrapper: correct PRESENT;
- `I don't want to call that checking...`: **false PRESENT** against the contemporaneous editorial/H4 disposition.

Result: **3/4** on the harder real regression set.

Interpretation: the narrow depersonalization test is useful but still over-flattens some first-person epistemic/classification stance. T01 is **not ready as a low-effort clearing auditor**.

**T10 low**
- RT2 `You don't have to settle that before...`: **false ABSENT**;
- B2 `You don't have to keep producing new versions...`: **false ABSENT**;
- inner-monologue visualization permission: ABSENT under the attempted label.

The two known model-shaped permission endings were missed because the new auditor treated local motivation as sufficient to make permission syntax earned.

More importantly, the supposed inner-monologue ABSENT control was never a tell-specific owner/editorial ABSENT judgment; it was inferred from a repair guide that actually asked to merge/demote the permission form. The T10 negative-control premise is therefore unreliable.

Interpretation: **reject the attempted T10 calibration architecture**. T10 currently lacks a trustworthy gate-passing negative control. Do not keep refining against invented negatives. Treat T10 as manual/editorial or advisory until a direct tell-specific negative control exists.

**T11 low**
- cross-domain holdout: **4/4**;
- real connective-tissue PRESENT regression: correct;
- necessary Romance time/phase bridge ABSENT regression: correct.

Result: **6/6** across seeded holdout + real regression, with zero thinking tokens in the low run.

Interpretation: T11 is the only one of these three tells with current evidence supporting a **low-effort narrow auditor**. This remains a small seeded calibration, not an accuracy estimate.

### Production routing consequence

Do not promote global V2 or V2.1.

Current economical routing is:

1. optional Jev positive triage;
2. compact Claude global sweep when the whole catalog needs review;
3. tell-specific narrow auditor only when that axis has real calibration evidence;
4. T11 may use the low-effort narrow auditor on the current prompt/configuration;
5. T01 remains manual/editorial or higher-rigor advisory until its epistemic-stance boundary is better calibrated;
6. T10 remains manual/editorial/advisory until a genuine gate-passing negative control exists;
7. no ABSENT from Jev or an uncalibrated narrow auditor may clear a tell.

No Pangram calls were used.

