# ChatGPT Operating Guide — Pangram Humanization Lab

This private repository is the canonical detector-research store for Joel Rosenblum article humanization work. Fresh chats should inspect GitHub directly rather than asking Joel to paste logs/results already committed here.

## Start here

**Always begin with `state/LESSON-INDEX.md`.** It is the canonical retrieval entry point and controls the current lesson read order, authority order, branch-specific evidence routing, and the lesson-closeout requirement. Do not hard-code an older lesson sequence from memory.

After the index directs you:
1. read the current promoted lesson summaries it names;
2. open the relevant case-study / incident note under `state/` only as needed;
3. inspect the relevant `cases/<case-id>/history.json` and round `plan.json`, `review.json`, `stats.json` when interpretation depends on exact experimental evidence;
4. for detector disputes or newer incidents, follow the branch instructions in `state/LESSON-INDEX.md` and inspect the cited branch rather than assuming `main` contains every raw experiment.

If the case ID is unknown, inspect recent commits for `state: rXX analysis` / `state: rXX deterministic stats` and open the changed case path.

## Division of labor

Joel/model does the human editorial work. The lab does repetitive detector science: controlled probe design, blind semantic/editorial review, Pangram submit/cache/poll, preregistered exact repeats, interaction analysis, falsification, stopping rule, and durable GitHub evidence.

Do not send Joel through manual chains of one-off detector variants when the lab can run them.

## Learning closeout is a completion gate

Before reporting any substantive editorial/detector/reconstruction/experiment pass complete:

1. identify each actual new finding;
2. disposition it in `state/LESSON-LEDGER.json` via the current `pangram-lesson-closeout` command;
3. use `promoted`, `provisional`, `article-specific`, `superseded`, or `no-new-lesson` as appropriate;
4. for anything promoted, update `state/LESSON-INDEX.md` and a current `state/WORKING-LESSONS*.md` summary;
5. run the repository closeout check/audit and verify it passes;
6. only then claim completion.

Read `docs/LESSON-CLOSEOUT.md` for exact commands and cross-branch handling. Do not ask Joel to remember or periodically police this process. GitHub CI and the weekly audit are the backstop.

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

Raw/cached detector evidence and experiment histories stay here. Promote only durable editorial lessons into the current canonical lesson summary/index, with provenance, tested boundary, what was falsified, repeats/version, and whether the finding is local or cross-case replicated. If/when the separate canonical `u-dont-existDOTcom/joel-articles` repository is available, durable article-skill lessons should also be synchronized there according to its repository map.
