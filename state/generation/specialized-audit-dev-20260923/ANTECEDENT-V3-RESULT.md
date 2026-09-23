# Specialized antecedent audit v3 — GPT-6 Sol result

Date: 2026-09-23
Status: DEVELOPMENT SUCCESS / NARROW AUDITOR PROMISING / NOT A GLOBAL AUTHORSHIP CLASSIFIER / NO PANGRAM CALLS

## Configuration

- model: `openai-gpt-6-sol`
- prompt SHA-256: `53248de48eae76e1d760436ffa30853633f610b46d74bd4ad0503f46977c5cb8`
- cases SHA-256: `23f72f62e45d724625de57dc5e24b84c6140a0474e1f7768b660d3a16d786346`
- hidden key SHA-256: `c407e6c05f2dffc1de1843fc0e91552978a5674fcb9840f728bc33bb22137fdf`
- deployment: `d4e33484-ba6c-459a-a127-885c81d06181`
- valid results: 4
- transport errors: 0
- Pangram calls: 0

## Score

**4/4**

1. Broken Inner Monologue target without source setup — expected FAIL, got FAIL.
   - correctly isolated quoted `“ask”` as the material orphan;
   - correctly treated `the usual inner-child prompt` as generic/bridging rather than automatically orphaned.
2. Exact same target with `“Voice,” “ask,” and “answer”` restored immediately before it — expected PASS, got PASS.
3. Known Human/no-AI self-contained paragraph — expected PASS, got PASS.
4. Controlled corruption deleting the antecedent for `They` — expected FAIL, got FAIL.

## Why v1/v2 controls were misleading

Earlier antecedent controls mixed two different questions:
- whether an excerpt omitted wider-document context;
- whether editing itself deleted setup required by the target.

One supposed Human PASS control began with `also` and named `Ball` while deliberately hiding the prior context, so FAIL was linguistically legitimate.
Another supposed PASS tested the source setup sentence itself rather than the later sentence whose `“ask”` reference depends on that setup.

V3 holds the target constant where possible and manipulates only antecedent availability.

## Process lesson

For narrow coherence audits, calibrate the exact observable operation with controlled context ablations/restorations.

Do not ask the critic to infer Human/AI authorship.
Do not use arbitrary excerpts whose omitted context creates artificial orphaning.
Do not treat every generic noun phrase as a required backward reference.

This result supports a specialized antecedent auditor as advisory/blocking coherence evidence after further same-axis coverage. It does not certify other axes and does not justify a global Human/AI PASS.
