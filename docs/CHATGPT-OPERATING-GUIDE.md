# ChatGPT Operating Guide — Pangram Humanization Lab

This private repository is the canonical detector-research store for Joel Rosenblum article humanization work. Fresh chats should inspect GitHub directly rather than asking Joel to paste logs/results already committed here.

## Read before detector claims

1. `README.md`
2. `state/WORKING-LESSONS.md`
3. relevant case-study file under `state/`
4. relevant `cases/<case-id>/history.json`
5. round `plan.json`, `review.json`, `stats.json` when interpretation depends on them

If the case ID is unknown, inspect recent commits for `state: rXX analysis` / `state: rXX deterministic stats` and open the changed case path.

## Division of labor

Joel/model does the human editorial work. The lab does repetitive detector science: controlled probe design, blind semantic/editorial review, Pangram submit/cache/poll, preregistered exact repeats, interaction analysis, falsification, stopping rule, and durable GitHub evidence.

Do not send Joel through manual chains of one-off detector variants when the lab can run them.

## Paid-call safety

Before any new Pangram submission:
- inspect exact-text cache and pending task state;
- reuse completed matching results;
- resume checkpointed task IDs instead of re-POSTing;
- preserve ambiguous POST failures without automatic repost;
- preserve wrong-version/terminal raw responses as evidence;
- keep GitHub durable before another paid call.

As of the v2.0.1 repair, the proven async path uses `x-api-key`, explicit `model: "pangram-4"`, expected terminal `version: "4.0"`, task-ID checkpoint before polling, content-addressed cache reuse, and fail-closed behavior after ambiguous submit. Read current code/README before assuming this has not changed.

## Local runtime

Normal location on Joel's Zorin machine:

`~/Téléchargements/pangram-humanization-lab-v2`

Typical update/resume:

```bash
cd ~/Téléchargements/pangram-humanization-lab-v2
git pull --ff-only
./INSTALL-AND-RUN.sh
```

For new endpoint pairs, use the current repo README/CLI help rather than an old remembered invocation.

## Interpretation

- Human editorial quality, semantic sanity and fidelity outrank Pangram.
- Exact submitted boundary matters; short samples are less reliable.
- Preserve nulls and counterexamples.
- Test interactions; do not infer magic words from one case.
- Pangram green does not justify stopping if a real thought thread remains.
- Pangram red does not justify worse prose or altered meaning.
- Stop once the local hypothesis is adequately discriminated; avoid token hunting.

## Promotion boundary

Raw/cached detector evidence and experiment histories stay here. Promote only durable editorial lessons into the canonical `u-dont-existDOTcom/joel-articles` repository, with provenance, tested boundary, what was falsified, repeats/version, and whether the finding is local or cross-case replicated.
