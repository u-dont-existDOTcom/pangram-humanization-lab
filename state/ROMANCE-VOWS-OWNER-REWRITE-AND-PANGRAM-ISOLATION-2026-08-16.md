# Romance Vows — direct owner rewrite + Pangram isolation

**Date:** 2026-08-16  
**Status:** editorial/evidence state; not canonical article authority; no article installation  
**Branch:** `automation/pangram-fixed-batch`

## Authority decision

Joel supplied a new direct rewrite of `Why marriage vows are dishonest` on 2026-08-16 after reporting that the prior assistant realization was mostly AI and that he had both humanized and improved it. This direct owner rewrite supersedes the developmental Vows candidate in `state/ROMANCE-VOWS-AUTHORITY-RESTORATION-2026-08-16.md`, older r27/r28 owner-final wording where the new rewrite differs, and later assistant candidates.

The new rewrite also supersedes two earlier routing inferences:

- The direct owner version explicitly restores `Marriage itself is a contract. How can you sign a contract about your heart?` in Vows. Preserve it even though locked Slow contains related contract/heart material. Direct owner recurrence outranks the earlier dedup inference.
- The direct owner version stops after the `murky middle` paragraph. Do not append the older conclusion merely because it once belonged to an owner-final version.

Detector status does not create this authority. The direct owner rewrite controls because Joel wrote it and selected it. The Pangram work below is research about which changes mattered to the detector.

## Exact owner endpoint tested

The following text is preserved exactly as supplied for the detector experiment. Do not silently copyedit these bytes when citing the experiment.

```text
Why marriage vows are dishonest
Conventional marriage vows are dishonest, and most people know it. Marriage itself is a contract. How can you sign a contract about your heart? Being sincerely in love at the wedding tells me what I feel then. It doesn't tell me what I'll feel ten years later.
I’d rather vow to tell the truth, keep showing up, support our children as best I can, or whatever else I genuinely believe I’m capable of delivering. Even “I’ll love you to the best of my ability, in accordance with how you love me” is something I could actually mean. But “I’ll always love you more than anyone else”—based on what? Because God wants me to?
We also find something like my warning in the New & Old Testaments. Ecclesiastes 5:4–6 teaches that it's better not to make a vow than to make one and not fulfill it. It warns that God will be angry with your words and destroy your work if you say to the priest, "I didn’t mean what I promised." It's also interesting that promising itself is almost an indicator of dishonesty. Jesus, in Matthew 5:33–37 (and  James 5:12), teaches that believers should let their "Yes" be "Yes" and their "No" be "No," warning that anything beyond this comes from Satan.
Where did the idea of promising to have romantic interest in your partner come from, anyway? It turns out it never existed in any culture I'm aware of until the Victorian age, when romantic feelings were elevated in England to the status of immutable truth.
The harder part for me has been what exclusivity is supposed to mean. For example, B. wanted to marry me, but I was still attracted to other women. I told her, “It’s not fair of me to commit to you if I’m still attracted to other women, so before I do, let me see if I can fix that.”
I meditated for a while and surprised my own self to find something like a switch in my mind. It felt like evolutionary programming around whether I had found my life mate and true love. I asked myself, “Is she the one?” The answer was yes, predictably, since I'd never been in love with anyone else. So I flipped off the mate-finding switch.
It worked about 99% of the time. I was no longer interested in other women, aside from one extremely beautiful girl who grabbed my glance once momentarily. That amazed me, although B. never quite believed the switch was real. She even started hallucinating that I was looking at or talking to other women when I wasn’t. So her jealousy was not simply tracking what I was doing in the present. More likely it was insecure attachment from childhood filtering her reality, although she blamed witchcraft.
Jealousy shows insecurity, but sometimes that insecurity can be an important indicator that the relationship actually is not secure, rather than just a remembered script from childhood. Although, either way, it can become a self-fulfilling prophecy. Have you ever noticed how unattractive jealous partners are, or is that just me?
Instead of stewing in jealousy and throwing out microaggressions now and then, open up. In a monogamous relationship, you might say:
“I notice you pay attention to this other girl more than me, and it makes me feel unloved and insecure. Can we talk about it? Do you really want to explore things with her? If so that's fine, but don't make the decision lightly because it's irreversible.”
In a polyamorous relationship the boundaries might be more negotiable, but that actually means negotiating is required.
I do believe two people can choose sexual exclusivity honestly. They can admit that attraction to other people exists and decide not to act on it each day.
I would rather make every attraction possible to mention casually, including the low-stakes ones. If only the serious attractions are supposed to be disclosed, each disclosure becomes such a major event that y'all are less likely to say anything at all.
But even if we choose sexual monogamy, I think it's worth understanding where it came from. Strict sexual exclusivity backed by law and social enforcement grew alongside agriculture, settled property, and inheritance, and became a mass norm during the Industrial Revolution. Tribal cultures across the world have generally had more flexible forms of primary partnership, or 'social monogamy,' with accepted ways for sexual or emotional connection to exist outside it.
Property and inheritance are still built into marriage, even while modern vows ask the same institution to guarantee a permanent romantic feeling.
That's not to say that polyamory is automatically better, because it can be dishonest too. These days, I believe (And an ex-leader of Tamera, maybe the most famous Free Love commune, agrees: https://www.facebook.com/martin.winiecki/posts/pfbid02V7nrbc7VLgPyLe91si9ximruTC7kwx2XjPBzUmUTnYr6sPViCPaTa7BxD2wmHAaJl ) it is often a way to cope with an inability to connect deeply with one person, or a way to admit a lack of self-control without necessarily doing the self-development that would make the arrangement ethical. That is not true of everyone, and it does not make polyamory wrong. If monogamy isn't something you actually live, admitting that is still more honest than promising it.
A lot of relationships end up in the murky middle between honest monogamy and polyamory. Partner deny outside attractions, try to suppress their changing feelings, and rely on possessiveness instead of real love.
```

- Word count: 897
- SHA-256: `1101efe49418bc47df63acb4c9916a1e39b2e8c4b64ac6ca1ff39e669e05dc95`

## Full-endpoint result

Experiment: `romance-vows-owner-rewrite-fixes-r1-2026-08-16`

The exact 897-word owner endpoint was Pangram 4.0:

- prediction: Human
- fraction Human: `1.0`
- fraction AI: `0.0`
- fraction AI-assisted: `0.0`
- window label: `Human Written`
- AI-assistance score: `0.1457953304052353`
- confidence: High

This establishes that the current exact owner endpoint is detector-green in the tested boundary. It does **not** tell us which of the many owner changes caused the full-section improvement, so controlled variants were required.

## Experiment 1 — Bible topology and ending package

Result file: `state/experiments/romance-vows-owner-rewrite-fixes-r1-2026-08-16-results.json`

### Bible boundary

| Variant | Change | Pangram 4.0 |
|---|---|---|
| `BIBLE_OWNER_SPLIT` | exact owner realization, including sentence split | Human, AI `0.0`, assistance `0.0697111189365387` |
| `BIBLE_PACKED_SAME_CONTENT` | same owner content packed into longer sentences | Human, AI `0.0`, assistance `0.10312946885824203` |
| `BIBLE_HISTORICAL_PACKED` | older formalized evidentiary realization | Mixed, AI `0.2023809552192688` |

The older formalized version produced one localized AI segment in the Ecclesiastes sentence. Packing itself did not reproduce the regression.

### Ending boundary

| Variant | Change | Pangram 4.0 |
|---|---|---|
| `ENDING_OWNER_STOP` | stop at Joel's new `murky middle` paragraph | Human, AI `0.0`, assistance `0.2939564883708954` |
| `ENDING_OWNER_PLUS_AFTERCARE` | append all three older closing moves | Mixed, AI `0.1885770559310913` |

The appended package was:

1. `Sometimes the concealment does more damage than an outside connection would have done.`
2. `Love is real. The form built around it can still be broken.`
3. `A foundational, permanent, exclusive romantic partnership is promised far more often than it is actually lived.`

The combined variant produced a terminal AI segment with assistance `0.627198338508606`, High confidence. That justified an interaction-isolation batch rather than assuming any one line was a magic trigger.

## Experiment 2 — controlled isolation

Result file: `state/experiments/romance-vows-owner-rewrite-fixes-r2-isolation-2026-08-16-results.json`

The same audit ID was retained so the six-call section budget could not be evaded.

### Bible result: formal source-certification realization, not packing or contraction

| Variant | Controlled change | Pangram 4.0 |
|---|---|---|
| `BIBLE_PACKED_IT_IS` | owner packed realization; only `it's` → `it is` | Human, AI `0.0`, assistance `0.11258269101381302` |
| `BIBLE_PACKED_EXPLICITLY_STATES` | owner packed realization; `teaches that it's better` → `explicitly states that it's better` | Mixed, AI `0.2010178118944168` |
| `BIBLE_PACKED_EXPLICITLY_STATES_IT_IS` | same phrase plus `it is` | Mixed, AI `0.20169492065906525` |

The two `explicitly states` variants reproduced essentially the same local regression. Their exact flagged Ecclesiastes windows scored AI-generated at approximately `0.55–0.58` assistance. The `it is` control remained entirely Human.

### Interpretation

For this fixed boundary:

- sentence splitting is **not necessary** for Human classification;
- sentence packing is **not sufficient** to cause the regression;
- contraction expansion `it's` → `it is` is a null in the tested owner realization;
- the formal source-certification realization `explicitly states that ...` is the variable that recreated the localized detector regression.

Do **not** promote `explicitly states` to a phrase blacklist. The useful prose-level lesson is broader and functional: formal source-reporting language that sounds like an evidentiary verification scaffold can become model-shaped in a boundary where plain authorial reporting (`teaches that...`) does not. Preserve source accuracy, but prefer the simplest natural relation to the source rather than narrating verification work.

The exact owner split still had the lowest assistance score among the tested versions, so the split is a good owner realization even though the experiment shows that splitting by itself is not what made the boundary Human.

### Ending result: cumulative overcompletion interaction

| Variant | Appended after owner stop | Pangram 4.0 |
|---|---|---|
| owner stop | nothing | Human, AI `0.0` |
| `ENDING_PLUS_CONCEALMENT_ONLY` | concealment consequence only | Human, AI `0.0`, assistance `0.3491256833076477` |
| `ENDING_PLUS_LOVE_FORM_ONLY` | `Love is real...` only | Human, AI `0.0`, assistance `0.33969536423683167` |
| `ENDING_PLUS_FOUNDATIONAL_ONLY` | foundational-partnership line only | Human, AI `0.0`, assistance `0.30479782819747925` |
| all three together | complete older closing package | Mixed, AI `0.1885770559310913` |

No single appended closing thought recreated the regression. The package did.

### Interpretation

This is strong local evidence for **cumulative overcompletion** rather than a lexical trigger. Each sentence is individually plausible and detector-green. Stacking all three after a paragraph that already lands the thought produces the model-shaped tail.

The durable editorial lesson is therefore not `delete sentence X`. It is:

> When the thought has already reached a real stopping point, several individually defensible consequences, summaries, or thematic closers can interact into an overcompleted tail. Audit the package function, not just each sentence in isolation.

This aligns with the existing article-level rule: optimize for the next necessary move, not conceptual completeness. A sentence can be fine alone and still be unnecessary in the actual chain.

## What the experiments do and do not establish

The owner rewrite changed far more than the two isolated variables above. It restored concrete lived material and idiolect, altered the B. experiment, retained the witchcraft detail, added the jealousy aside, restored `y'all`, added the Tamera attribution/link, and stopped earlier. Because the whole endpoint bundles those changes, the experiments **do not establish** that formal citation language and cumulative aftercare fully explain the original assistant section's detector result.

They do establish two reproducible local mechanisms inside the current Vows boundary:

1. formal source-certification wording can create a localized AI segment where the same substantive source claim in plainer owner language remains Human;
2. multiple individually Human closing sentences can become AI-like as an overcompleted package after the thought has already landed.

These are interaction/topology lessons, not magic-word rules.

## Editorial cold audit

### Heading fit and semantic sanity

The owner opening answers `Why marriage vows are dishonest` immediately through the mismatch between present sincerity and claims about future feeling. It gives promiseable actions, then asks where permanent romantic-interest promises came from.

`The harder part for me has been what exclusivity is supposed to mean` is a live turn, not a generic transition. The B. experiment changes the case: Joel tried to alter his attraction, largely succeeded by his report, yet jealousy persisted. The next pressure is therefore whether jealousy reflects current relationship information, remembered insecurity, or both. The disclosure example and negotiability paragraph follow from that problem.

The later history of exclusivity arrives only after Joel has established chosen sexual exclusivity as something he thinks can be honest. Polyamory then complicates rather than symmetrically resolves the question.

### Reality and curious-reader chain

The section repeatedly returns to ordinary relational pressures: attraction, jealousy, insecurity, disclosure, daily choice, possessiveness, and the practical meaning of an exclusivity agreement. The personal B. sequence carries the argument instead of serving as ornament for a prefabricated taxonomy.

### Stopping point

The new final `murky middle` paragraph is a valid stopping point. It returns the historical and personal strands to the live problem of what people actually do with outside attraction. The controlled Pangram interaction is secondary evidence that appending three further conclusion moves overcompletes this boundary. More importantly, the reader does not need those sentences to understand the thought.

### Fidelity and provenance

- Current controlling prose: direct Joel rewrite supplied 2026-08-16.
- Detector variants: synthetic controlled probes; never article authority.
- Older r27/r28 and Aug. 16 developmental candidate: superseded where they differ.
- Locked Slow remains locked, but its related contract/heart wording no longer authorizes deletion from Vows because Joel directly restored the recurrence.

## Factual verification boundary

This detector task did **not** verify the empirical/historical claims about Victorian-era romance, agriculture/inheritance, tribal social monogamy, biblical interpretation, or Tamera. Detector success is not evidence for those claims. Any factual/source audit should be run separately and should not silently rewrite the owner endpoint.

## Publication-level cleanup is separate

The detector endpoint intentionally preserves exact owner bytes. A later P1 copy pass may inspect such literal issues as:

- `Partner deny` → likely `Partners deny`;
- double space in `(and  James 5:12)`;
- punctuation/capitalization around the Tamera parenthetical.

Do not fold such cleanup into detector provenance retroactively.

## Call accounting and stop rule

Ledger: `state/pangram-call-ledgers/romance-vows-owner-rewrite-fixes-2026-08-16.json`

- `vows-bible-topology`: 6/6 paid calls, estimated 6 credits / $0.30; **cap exhausted**.
- `vows-ending-aftercare`: 5/6 paid calls, estimated 5 credits / $0.25.
- `vows-full-owner-rewrite`: 1 paid call, estimated 1 credit / $0.05.
- total: 12 paid calls, estimated 12 credits / $0.60.
- pending resumes: 0.

Stop. The remaining ending call should not be spent on phrase hunting. The interaction has been isolated sufficiently for the article-level lesson.

## Next editorial use

Use the direct owner Vows rewrite as the Vows source in the whole-article restoration/assembly. Preserve the current stopping point. Preserve the owner-restored contract/heart line despite the related locked Slow passage. Apply publication-only cleanup separately from detector evidence. No more Vows detector work is warranted absent a new concrete defect or a materially different future detector/version.
