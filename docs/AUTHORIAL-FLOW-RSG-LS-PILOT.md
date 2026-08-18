# Recurrent Source-Gated Live Selection (RSG-LS) pilot

Status: **experimental / provisional.** This is the next issue #41 feasibility condition after the static authorial-state and full-source recurrent conditions. It is not a promoted humanization rule.

Date: 2026-08-18

## Question

Does recurrently revealing only the source element that has become live **now** reduce fact-to-sentence serialization and premature completion, while preserving the complete authoritative meaning through a separate controller/fidelity layer?

This pilot deliberately avoids claims about hidden cognition. `live state`, `pressure`, and `generation function` are task-level representations inferred from observable prose and source evidence.

## Roles

### CONTROLLER

CONTROLLER has authority over **selection**, not prose.

CONTROLLER sees:

- the complete authoritative source/claim ledger;
- all source IDs already revealed;
- prose-so-far;
- fixed semantic, certainty, actor, causality, chronology, quotation, and protected-function constraints;
- previously rejected/deferred selections.

CONTROLLER never writes the candidate passage and never tells WRITER what connection to make.

At each turn CONTROLLER returns `REVEAL` with exactly one source ID and a hidden analysis `FUNCTION`, or `STOP`.

Allowed provisional generation-function labels:

- `CONCRETIZE`
- `COMPLICATE`
- `TEST`
- `QUALIFY`
- `COUNTEREXAMPLE`
- `REFRAME`
- `ANALOGIZE`
- `RECALL`
- `SELF_IMPLICATE`
- `APPLY`
- `RESOLVE`
- `REOPEN`
- `OTHER`
- `UNKNOWN`

CONTROLLER must select on the basis of what the **existing prose** makes live. It must not select merely because an item remains unused, preserve source order by default, distribute examples evenly, or steer toward a preselected ending.

Useful reasons to reveal an element include that it now concretizes, complicates, falsifies, tests, distinguishes, exemplifies, personalizes, or changes the meaning of the live thought. `STOP` is allowed even with unrevealed source elements if none is presently live. Coverage is handled outside selection; a coverage conflict can later trigger rollback/re-entry rather than forcing the next unused fact into prose.

### WRITER

WRITER has authority over whether the currently available material has generated something sayable.

WRITER sees only:

- all source elements revealed so far, as an unordered cumulative pool; and
- accepted prose-so-far.

WRITER never sees:

- unrevealed source elements;
- source order or source-position metadata;
- remaining-coverage count;
- paragraph or article outline;
- target conclusion;
- CONTROLLER's selection rationale or `FUNCTION` label;
- evaluator labels.

WRITER returns `MORE` if the available material has not generated an actual thought worth expressing, or the natural amount of new prose that has become sayable.

Rules:

1. Do not paraphrase the newest source element merely to use it.
2. Do not turn every available element into prose.
3. Let multiple available elements interact before writing when that is what the material requires.
4. Do not preview a conclusion simply because one is inferable from the source inventory.
5. Do not add memories, beliefs, causal claims, certainty, or rhetorical functions absent from the licensed material.
6. If a thought has landed, do not append explanatory aftercare or recap merely for completeness.
7. A new output is a **candidate move** until the separate gates accept it.

### FIDELITY GATE

FIDELITY sees the authoritative source/claim ledger, accepted prose, and candidate delta. It outputs `PASS` or `FAIL` plus the smallest explicit unsupported/changed relation.

It checks meaning only: claims, certainty, actors, chronology, causality, attribution, quotations/identity strings, autobiographical stance, and protected rhetorical function. It does not decide whether the candidate is a natural next thought.

### FLOW GATE

FLOW sees accepted prose plus the candidate delta but not the source ledger, unrevealed source inventory, or source order. It outputs:

- `PASS`;
- `BAD_EDGE`;
- `OVERCOMPLETION`; or
- `NATURAL_STOP`.

It asks whether the candidate is an earned continuation from the live state rather than merely topically related. Later material cannot retroactively rescue a bad entry edge.

## Why the roles must be isolated

A valid source-gating experiment cannot run CONTROLLER and WRITER in one shared model conversation, because the WRITER would already have latent access to the unrevealed source packet. The repository runner therefore invokes each role through a fresh **ephemeral Codex process**. CONTROLLER receives the full packet; WRITER receives only the accepted prose and the cumulative revealed pool; FLOW is source-blind. The cumulative WRITER pool is deterministically reordered by source ID hash so neither original source order nor reveal order is exposed.

This is an experimental-control requirement, not a claim that ordinary production must use separate models.

## Turn protocol

For each turn:

1. Compute a hash of the accepted prose-so-far.
2. CONTROLLER chooses one unrevealed source ID or `STOP`.
3. If `REVEAL`, add that source item to WRITER's cumulative available pool. Do not disclose `FUNCTION` or source-position information.
4. WRITER returns `MORE` or a candidate prose delta.
5. If `MORE`, record the event and return to a fresh CONTROLLER call. Nothing is added to prose.
6. If WRITER emits prose, run FIDELITY and FLOW separately.
7. Only a candidate passing FIDELITY and receiving `PASS` or `NATURAL_STOP` from FLOW becomes accepted prose.
8. A rejected candidate is retained in the local trace and the feasibility run stops rather than automatically paraphrasing until a judge accepts it.
9. After acceptance, recompute the live state from the new prose; do not reuse the old controller ranking.
10. CONTROLLER may `STOP`. If authoritative coverage is complete, terminate. If coverage remains but nothing is live, record a **coverage/flow conflict** rather than forcing an unused source item into the old trajectory.
11. `NATURAL_STOP` behaves the same way: with unused authoritative material it records a coverage/flow conflict; with complete coverage it terminates successfully.

## Automated local runner

Raw source packets and generated prose remain local and are excluded from Git under `.local/authorial-flow/`. The committed trace contains hashes and structural/manual labels only.

After installing the repository branch, run:

```bash
pangram-lab authorial-flow-rsg-ls .local/authorial-flow/relationship-spirit-packet.json
```

Optional controls:

```bash
pangram-lab authorial-flow-rsg-ls \
  .local/authorial-flow/relationship-spirit-packet.json \
  --model gpt-5.6-sol \
  --reasoning-effort xhigh
```

The runner checkpoints after every turn. Re-running an already terminal experiment with the same exact packet hash returns the saved result without buying or duplicating model work. Pangram is not called by this command.

The local packet shape is:

```json
{
  "schema_version": "authorial-flow-rsg-ls-input/v1",
  "experiment_id": "relationship-spirit-feasibility-001",
  "source_items": [
    {"id": "s1", "position": 1, "text": "<authoritative source element>"},
    {"id": "s2", "position": 2, "text": "<authoritative source element>"}
  ],
  "initial_revealed_source_ids": ["s1"],
  "initial_prose": "<accepted prose at the checkpoint, or empty>",
  "constraints": ["<fixed fidelity/protected-function constraint>"],
  "max_steps": 12
}
```

For a continuation of an already-run recurrent-accumulation pilot, put every source element that had already been revealed into `initial_revealed_source_ids` and put the exact accepted prose checkpoint in `initial_prose`. This lets the new condition continue from the existing evidence rather than regenerating it.

## Trace contract

Do not commit raw private prose or source packets to Git. The canonical experiment trace may contain source IDs, source positions, hashes, manual labels, model/version metadata, and local artifact references. A local ignored trace may additionally contain the actual text needed to run the experiment.

Minimal metadata trace shape:

```json
{
  "schema_version": "authorial-flow-rsg-ls/v1",
  "experiment_id": "relationship-spirit-feasibility-001",
  "condition": "RSG-LS",
  "source_packet_sha256": "<64 hex>",
  "initial_prose_sha256": "<64 hex>",
  "initial_revealed_source_ids": ["s1"],
  "initial_revealed_source_positions": {"s1": 1},
  "model": {"provider": "<provider>", "name": "<name>", "version": null},
  "steps": [
    {
      "step": 1,
      "controller_action": "REVEAL",
      "selected_source_id": "s3",
      "selected_source_position": 3,
      "selection_function": "COMPLICATE",
      "revealed_source_ids_after": ["s1", "s3"],
      "writer_action": "MORE",
      "candidate_delta_sha256": null,
      "accepted_prose_sha256_after": "<64 hex>",
      "manual_immediate_discharge": null,
      "discourse_relation": null,
      "fidelity_label": null,
      "flow_label": null
    }
  ]
}
```

`manual_immediate_discharge` is intentionally a reviewer annotation, not a lexical-overlap heuristic. Academic writing-process research warns that observable process events are not uniquely interpretable as cognitive events; this pilot preserves that same separation between observation and inference.

## Deterministic summary metrics

The repository helper computes only metrics derivable without semantic inference:

- initial revealed count;
- reveal count;
- stop count;
- write count;
- `MORE` count/rate;
- number of available source elements at each emitted move;
- mean/min/max accumulation depth before emitted moves;
- source-position monotonicity / exact-next-position use for newly selected material;
- counts of manually supplied immediate-discharge, fidelity, flow, discourse-relation, and generation-function labels.

It must **not** infer thought occurrence, immediate discharge, causality, or authorial authenticity from pause length, lexical overlap, or one scalar score.

## Feasibility packet

The first run continues the relationship-spirit case already recorded in issue #41. Preserve those existing pilot outcomes as controls rather than regenerating them. The RSG-LS run should start from the same frozen source/claim packet and the accepted recurrent-accumulation checkpoint, then compare its trace against:

- static authorial-state card;
- recurrent generation with the whole source packet visible;
- recurrent accumulation with `MORE`.

No paid Pangram call is warranted for this feasibility run. First require clean fidelity, a reduction in immediate source-to-sentence discharge, and no regression in stopping/overcompletion. If those conditions hold across more than one source packet, then idiolect/LUAR and a tightly budgeted Pangram comparison become informative secondary measurements.

## Success / failure interpretation

A positive feasibility result is not "the prose sounds better." It is a trace in which new prose is repeatedly delayed until available ideas interact, controller selections respond to the changed prose rather than source order, accepted moves pass fidelity independently, and the passage reaches a natural stop without systematic aftercare.

Failure includes any of the following:

- CONTROLLER walks the source list in order without live justification;
- WRITER converts each reveal into an immediate sentence;
- `FUNCTION` labels become instructions that leak into WRITER;
- unrevealed inventory, source positions, or destination information leak to WRITER;
- fidelity is sacrificed for a more interesting transition;
- the system must force leftover source material into a thought that has naturally ended.

If this condition fails because the cumulative available pool itself becomes an outline, the next reduction should test bounded/decaying availability rather than adding stylistic imitation instructions.
