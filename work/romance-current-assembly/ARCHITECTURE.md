# Romance architecture map

<!-- article-id: romance -->

Indexes the current private Romance reconstruction. This graph is a visual recovery/control surface, not prose authority. Current explicit Joel corrections and the relevant `state/ROMANCE-*.md` records outrank the graph if a conflict is ever found.

Current materialized master: `work/romance-current-assembly/current-master.md` SHA-256 `4c3f58cb4e61eb8a194e0a183f3ec443e84155cdafc08124642ef68d98caeb5c`.
Current reader-visible boundary SHA-256: `99c803c7eda079582a8ba76b6524dcf726ece42e44e8f85796438b929594ea40` (18,357 words).
Whole-article cold-audit record: `state/ROMANCE-CURRENT-MASTER-COLD-AUDIT-2026-08-16.md`.

## Article overview

```mermaid
flowchart TD
    opening["Opening: father quote, missing romance curriculum, scope"]
    love["What we mean by love: agape and eros"]
    talk["Talk before sex: making love, honesty, casual sex"]
    should["Should you be in a relationship: readiness and loneliness"]
    starting["Starting on the right foot: discern before attachment closes"]
    crucible["Crucible: intimacy activates wounds and growth"]
    primal["Primal attraction: polarity inside safety"]
    twin["Twin Flames: de-ontologize deep connection"]
    pillars["Two Pillars: couple needs shared community"]
    choosing["Choosing together: agreements, vows, exclusivity"]
    conscious["Doing it consciously: imagination and psychedelic integration"]
    already["If already in it: trust, honesty, agape, outside help"]
    children["Children: obligations that survive adult romance"]
    ending["Ending consciously: leave, aftermath, learn from loss"]
    tough["Tough Love: cultural and spiritual synthesis"]
    bear["Bear and Rumi: return to opening and stop"]

    opening --> love --> talk --> should --> starting --> crucible --> primal --> twin --> pillars --> choosing --> conscious --> already --> children --> ending --> tough --> bear
```

## Non-linear dependencies

```mermaid
flowchart LR
    opening["Father sex talk"] -. "terminal callback" .-> bear["Bear sex talk"]
    love["Agape and eros"] -. "agape under pressure" .-> already["If already in it"]
    should["Readiness question"] -. "relationship reveals readiness" .-> crucible["Crucible"]
    starting["Idealization and attachment window"] -. "discernment tools" .-> conscious["Imagination and psychedelics"]
    pillars["Shared community"] -. "outside help" .-> already["If already in it"]
    pillars -. "children need a village" .-> children["Children"]
    pillars -. "witnesses during conflict" .-> ending["Ending consciously"]
    pillars -. "final cultural synthesis" .-> tough["Tough Love"]
    ending -. "lessons from B K H" .-> tough
```

## Community thread drill-down

```mermaid
flowchart TD
    dyad["Problem: isolated dyad carries too much"]
    pillars["Two Pillars: shared friends and community"]
    conscious["Why this sounds artificial: missing communal functions"]
    already["If already in it: mutual friend, peer counselor, therapist, group"]
    children["Children: stability should not rise and fall with romance"]
    ending["Ending: friends can witness and mediate rather than take sides"]
    tough["Tough Love: sealed private dyad creates conditions for pathology"]

    dyad --> pillars
    pillars --> conscious
    pillars --> already
    pillars --> children
    pillars --> ending
    pillars --> tough
```

## Current authority status

- **Opening:** Aug. 15 direct owner-final opening is materialized.
- **Doing it consciously / Psychedelics:** Aug. 16 approved boundary is materialized, including the sober long-term therapy test, delayed kind-conversation ritual, and current artificiality paragraph.
- **If you're already in it:** Aug. 16 direct owner-final rewrite is materialized; owner text SHA-256 `d513198739e921e81400f37bd5137ff5ba5635720cf10e87b1a95d41da110c16`; owner reports fully Human / High confidence.
- **Children:** current owner-final function is materialized: co-parenting responsibility, stepchildren continuity, never recruiting children into the adult war, the Bear custody/contact case, and the village return. The later reconstructed `Mommy and Daddy arguing` speech and `ordinary case / extreme exception` bridge are excluded from the master and remain provenance only.
- **Ending consciously:** the conversational owner-final Ending / After leaving / What I gained block remains in place. No child-speech relocation or older formal source was imported.
- **Tough Love:** corrected Aug. 16 direct owner-final section is materialized; owner text SHA-256 `ed0dd5037ca75523d3466ad9f26d21cd0aefa9f3a6532991c4e73009ac9185d8`; owner reports fully Human / High confidence.
- **Terminal close:** Bear/Rumi is inside current Tough Love and is the only terminal prose. Nothing follows it except the native Subscribe object.

## Cold-audit disposition

- Community recurs deliberately because it performs different causal jobs at different nodes; do not deduplicate by noun overlap.
- H. recurs as different evidence at different nodes; do not collapse the cases automatically.
- The Children transition `Never recruit children into the adult war` → Ann/Bear case is intentionally direct; do not generate a bridge unless Joel asks for one.
- Largest retained recurrence: Rumi appears once in `What I gained from loss` and once in the final sentence. The first belongs to loss; the second is the current owner-final universal/terminal close. Retain unless Joel chooses a single Rumi use or the final whole-article detector localizes that boundary.

## Protected placement rules

1. Do not move or delete a section merely because a nearby detector span is red. Check this map and the article-wide architecture first.
2. A section may recur around the same person or concept when it performs a different job. Inspect the labeled function before calling it duplication.
3. Before deleting or relocating prose, identify every job/dependency it carries and where each job will land. If one becomes orphaned, the edit is blocked.
4. When Joel supplies a new owner-final section, update this map in the same change that updates the assembly spec/replacement file.
5. The map must represent the intended current article, while `current-master.md` and its manifest prove what has actually been materialized. A mismatch is explicit assembly drift to repair, never permission to reinterpret authority.
6. A surviving older source is not automatically current owner-final prose. Use it to recover protected thought/functions, but prefer later direct Joel rewrites and recorded locks.

## Current next step

Run exactly one Pangram 4.0 certification on reader-visible SHA-256 `99c803c7eda079582a8ba76b6524dcf726ece42e44e8f85796438b929594ea40`. If a problem localizes, inspect the corresponding graph node and dependency edges before any rewrite. Do not spend section-level calls merely to reproduce already-green owner-final sections.
