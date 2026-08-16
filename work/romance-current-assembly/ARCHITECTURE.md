# Romance architecture map

<!-- article-id: romance -->

Indexes the private Romance reconstruction currently assembled from the Aug. 13 baseline plus later owner-final replacements. This graph is a visual recovery/control surface, not prose authority. Current explicit Joel corrections and the relevant `state/ROMANCE-*.md` records outrank stale materialized bytes.

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
    conscious["Why this sounds artificial: instructions substitute for missing community"]
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

## Current authority and assembly drift

- **Opening:** Aug. 15 direct owner-final opening; current PR #32 replacement is authoritative for this node.
- **Doing it consciously:** the user approved the shorter two-sentence H1 opening plus the current Imagination section and the reconstructed `Why all of this sounds artificial` paragraph as High-confidence Human before adding the newer psychedelic material. PR #32 still carries the longer generic realism disclaimer and older artificiality ending.
- **Psychedelics:** Aug. 16 owner-approved integration adds the sober long-term test for therapy and the delayed kind-conversation ritual. The current PR #32 materialized master is stale here.
- **If you're already in it:** Aug. 16 direct owner-final rewrite, SHA-256 `d513198739e921e81400f37bd5137ff5ba5635720cf10e87b1a95d41da110c16`, owner-reported fully Human / High confidence. The current PR #32 materialized master is stale here.
- **Children:** current owner-final function is co-parenting responsibility, stepchildren continuity, never recruiting children into the adult war, the Bear custody/contact case, and the village return. The later reconstructed child-facing `Mommy and Daddy arguing` speech and its `ordinary case / extreme exception` bridge are not established as current owner-final authority and must not be moved elsewhere by inference. Remove them from the current assembly while preserving provenance outside the master.
- **Ending consciously:** the current conversational owner-final Ending / After leaving / What I gained block remains in place. Do not import the older formal `unilateral exit standing` source merely because it appears in earlier files, and do not relocate the reconstructed child speech here without a direct owner instruction.
- **Tough Love:** Aug. 16 corrected direct owner-final section, SHA-256 `ed0dd5037ca75523d3466ad9f26d21cd0aefa9f3a6532991c4e73009ac9185d8`, owner-reported fully Human / High confidence. The current PR #32 materialized master is stale here.
- **Terminal close:** Bear/Rumi is now inside the current owner-final Tough Love section and is the only terminal prose. Nothing follows it except the native Subscribe object.

## Protected placement rules

1. Do not move or delete a section merely because a nearby detector span is red. Check this map and the article-wide architecture first.
2. A section may recur around the same person or concept when it performs a different job. H. in casual/situationship, community, loss, and Tough Love is not automatically duplication; inspect the labeled function.
3. Before deleting or relocating prose, identify every job/dependency it carries and where each job will land. If one becomes orphaned, the edit is blocked.
4. When Joel supplies a new owner-final section, update this map in the same change that updates the assembly spec/replacement file.
5. The map must represent the intended current article, while `current-master.md` and its manifest record what has actually been materialized. Any mismatch is explicit assembly drift to repair, never a reason to silently reinterpret authority.
6. A surviving older source is not automatically current owner-final prose. Use it to recover protected thought/functions, but prefer later direct Joel rewrites and recorded locks.

## Current next step

Reconcile PR #32's assembly operations against this map: replace the full `Doing it consciously` boundary with the approved current version, replace `If you're already in it`, remove the two non-authoritative Children reconstruction paragraphs while leaving Ending untouched, and replace complete Tough Love; regenerate `current-master.md` and reader-visible boundary; then run two whole-article cold audits before the final Pangram call.
