# Humanization critic provenance holdout v2 — pre-run protocol

Date: 2026-09-22
Status: FROZEN / UNTOUCHED HOLDOUT / NOT YET CLASSIFIED / VENICE TRANSPORT CURRENTLY HTTP 402

## Purpose

This is the untouched validation set required after benchmark v1 became development data.

Benchmark v1 scored 14/20 under the prior rubric and was used to design the content-neutralized scaffold / Human-surplus correction. Therefore v1 can never again support a prospective calibration claim.

Holdout v2 is selected from passages not used in v1.

## Frozen design

- total: 20 passages
- HUMAN: 10
- AI: 10
- word range: 61–201
- v1 exact-SHA overlap: 0
- shuffle seed: 202609222350
- blind-samples SHA-256: `9afcdc6662c2a3df916b7cfd31037c630c19bef7182c657653d65b15da5e571a`
- hidden gold-key SHA-256: `288d15e33131ad499eba59d41ccb58e9cfd21f63cd31ed2fc9c5c65e68ddf7a0`
- classifier prompt: `state/generation/critic-benchmark-20260922/critic-prompt-v2.txt`
- classifier prompt SHA-256: `64f7d6cfdc8f577ee2fe6d5c4f6a0306205fe418937f86618c5120aaa48329e4`
- model alias planned: `gpt-5.6-sol`
- temperature: 0

Human labels use direct/natural Joel prose with explicit provenance. AI labels use explicit assistant/model prose. The set deliberately mixes therapy, relationship, and other Joel registers so topic is not a reliable label shortcut.

## Blind-key separation

The gold key is **not** stored on this branch or on canonical `main` before the run.

A separate private evidence branch stores the exact key. Do not fetch/read that branch in any classifier context or runner preparation context. After all 20 classifier responses and their hashes are frozen durably and an explicit end marker exists, a scoring context may read the key and compare outputs.

The gold-key SHA above is the pre-run commitment.

## Run rules

1. Do not change any sample bytes, ordering, prompt bytes, model alias, or temperature after the first valid classification response.
2. Send one stateless request per passage through the authenticated UDA model gateway.
3. External classifier receives only the frozen rubric + literal passage. It gets no tools, provenance, label, detector history, benchmark score, prior answer, or neighboring sample.
4. Capture provider response id/model, literal response, parsed classification, usage, elapsed time, sample SHA, prompt SHA, and transport errors.
5. Freeze all 20 valid responses before opening the gold key.
6. Transport errors are not classifier misses. Resolve transport and rerun only the affected sample with identical bytes/configuration.
7. A valid but wrong binary classification is a miss.
8. Required production-gate result: **20/20**. Anything lower leaves the fresh critic non-gating for Pangram admission.
9. If the rubric changes after seeing any v2 label/result, v2 immediately becomes development data and validation moves to holdout v3.
10. No Pangram calls are part of this benchmark.

## Current transport state

The same UDA Venice gateway successfully completed v1, then returned HTTP 402 Payment Required on all 20 attempted v2-development requests. Those were transport failures and produced no classifications. Do not run this untouched holdout until the external model transport can return a valid completion.

Railway Agent itself is not a substitute classifier: it now enforces Railway/DevOps scope and refused generic prose-classification tasks.
