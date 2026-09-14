# Somatic risk-reserve and edit-operator ledger — 2026-09-14

Status: WORKING DETECTOR-RESEARCH RECORD / OWNER-CORRECTED / NO NEW PANGRAM CALL

## 1. Correction

The earlier interpretation that Human-labeled manual paragraphs 'killed' the structural-risk rule was too strong.

The current working distinction is:

- **risk contribution**: a feature or edit can move prose toward Pangram's AI/Mixed boundary;
- **verdict**: the paragraph can still receive Human when other Human-shape evidence is strong enough.

A useful research abstraction is:

`observed_margin ~= protective_human_shape - ai_risk_burden + interactions`

This is not a claim about Pangram's literal internal algorithm. It is a model for organizing observed outcomes.

The manually humanized Somatic V4 positive control is therefore evidence that risky-looking structure can survive inside a Human paragraph; it is not evidence that all Human paragraphs have the same detector margin.

## 2. What the controlled experiment actually supports

Source: `state/experiments/human-to-ai-minimal-pairs-20260828/RESULTS.json`.

| Edit operator / realization | Cell(s) | Observed result | Direction | Evidence status |
|---|---|---|---|---|
| Polished abstract cross-domain transition on compact Somatic backbone | C2 | Mixed; 30.77% AI fraction | risk increase | direct controlled evidence |
| Explicit cross-domain relation, colloquial realization | C4 | Human; 0% AI fraction | lower risk than polished realization in same family | controlled realization evidence |
| Compression + polished cross-domain synthesis | C1 / C7 | AI; 100% AI fraction in both tested polished-synthesis variants | strong risk increase in tested backbone | replicated within one backbone family |
| Compression without explicit synthesis | C5 / C6 | Human; 0% AI fraction | null in tested backbone | controlled evidence |
| Paragraph packing only | C3 | Human; 0% AI fraction | null in tested backbone | single controlled cell |
| Taxonomy/list closure alone | B1 | Human; 0% AI fraction | null alone | single controlled cell |
| Polished connective tissue alone | B2 | Human; 0% AI fraction | null alone | single controlled cell |
| Taxonomy closure + polished connective tissue | B3 | Mixed; 13.21% AI fraction | interaction risk increase | controlled interaction evidence |
| Replace polished bridge with colloquial bridge while retaining taxonomy | B4 vs B3 | Human; 0% AI fraction vs Mixed | risk decrease | controlled realization substitution |
| Replace neat taxonomy closure with colloquial/open closure while retaining polished bridge | B5 vs B3 | Human; 0% AI fraction vs Mixed | risk decrease | controlled realization substitution |
| Explanatory completion | A1 | Human; 0% AI fraction | null in tested backbone | single controlled cell |
| Sentence equalization | A2 | Human; 0% AI fraction | null in tested backbone | single controlled cell |
| Explanatory completion + sentence equalization | A3 | Human; 0% AI fraction | null combination in tested backbone | controlled interaction cell |

### Working interpretation

The strongest repeated pattern in this packet is not 'compression is AI' or 'explicit relation is AI.' Compression survives by itself. An explicit relation survives in a colloquial realization. What repeatedly raises risk in the compact Somatic family is a **polished abstract relationship/synthesis operation layered onto compressed prose**.

The cancer-family cells show a second kind of interaction: taxonomy closure and polished connective tissue are both Human alone, but their combination becomes Mixed. Either a more colloquial bridge or a more open/colloquial closure restores Human.

This makes the detector evidence interactional and graded, not a phrase blacklist.

## 3. New reproducible manual positive-control audit

The previous note reported '9 of 89' but failed to preserve the exact nine row identities. That count is not being reused as row-level evidence.

Below is a **new, explicitly selected nine-paragraph boundary-risk set** from the same 89 substantive paragraphs. Selection was by close reading after the owner correction, so it is descriptive and non-blind. Every listed paragraph is owner-reported Human when tested individually.

Hâle's first-person Somatic Experiencing and Yin Yoga blocks are excluded from Joel-style learning. Joel's prose *about* Hâle is not needed for this nine-paragraph set.

| ID | Section | Words | SHA-256 (prefix) | Relative risk | Why it looks risk-bearing | What appears to compensate |
|---:|---|---:|---|---|---|---|
| 10 | Introduction / therapy map | 76 | `39186f30fda9ce56` | medium-high | taxonomy/spectrum compression; evidence caveat; broad synthesis into one map | explicit epistemic ownership ('this is mine'); irreverent peer-review aside; uneven conversational finish |
| 17 | Dominant trauma-memory therapies critique | 132 | `4c4d921f138e7d87` | high-ish | declared two-problem structure; parallel contrast; abstract causal argument; analogy used as a landing | named source; strong owned judgment; concrete adverse-event/dropout issue; child-discipline analogy |
| 25 | Somatic Experiencing / window of tolerance | 97 | `368d1d37b4df8ccd` | medium | three-part technical concept package with parenthetical glosses; clean explanatory progression | open disagreement with standard framing; vivid pool analogy; physical actions; personal evaluative language |
| 34 | Trauma-sensitive / restorative yoga | 92 | `e3d914ab1018593a` | medium | stage-to-stage progression; explicit body-mind relation; purpose-driven explanatory close | ordinary embodied actions; slightly awkward/redundant phrasing; concrete posture/stretching/meditation claims |
| 66 | Layer 4 / targeted memory work framing | 96 | `f82f53d8feda659a` | high | formal category announcement; abstract definition; fit distinction; explicit goal close; dense conceptual packaging | first-person category ownership; 'stickiness' metaphor; concrete flashback use case; non-academic wording mixed into formal explanation |
| 67 | EMDR mechanism | 93 | `683a0736dcfd9b95` | medium-high | textbook-style modality definition followed by mechanism and outcome sequence | concrete event examples; literal eye movement; explicit uncertainty; small quoted image ('I can handle this.') |
| 70 | Hypnosis / EMDR comparison | 76 | `ad0e5f7263d31f71` | medium-high | neat cross-domain comparison carried through several sentences; repeated relation-announcement | owned curiosity ('It's interesting'); historical specificity; hedging that interrupts the clean equivalence |
| 75 | Narrative and cognitive integration | 70 | `6d15d47ed3b3e1b8` | high-ish | layer-transition announcement; compressed summary of prior stages; explicit causal rationale; insurance contrast | blunt 'we're actually humans, not just animals'; owner thesis about ordering; conversational parenthesis |
| 88 | Outcomes / choosing therapies | 96 | `52294c3bd1294b3f` | medium-high | advice sequence with repeated evaluative steps and a final fit criterion; visible completion arc | 'zillion studies'; direct practical judgment; talking to actual people; 'dip your feet in' idiom |

### Exact selected paragraph texts

#### P10 — Introduction / therapy map

SHA-256: `39186f30fda9ce56fe86800c9d6361ec82bdf3435d3c4595f8091bd864040795`

Because specific somatic therapies are on a spectrum of physical<- >emotional (or conscious<->subconscious), as well as a spectrum of intensity and specificity, we can often guess which one might be right for someone at which time. These don’t all have the same level or type of evidence supporting them, and there’s definitely no scientific roadmap that could survive peer review, but ultimately everyone somehow builds their own map of what makes sense, and this is mine.

#### P17 — Dominant trauma-memory therapies critique

SHA-256: `4c4d921f138e7d87b08f420221b7d665963b96743154f199906f0e3e910e7ed5`

Those therapies do show meaningful impact for many people in terms of reducing hyperarousal, and sometimes dissociation. But there are two main problems with them that Peter Levine, et al. have explained. On the one hand, as Levine points out, exposure desensitization therapy can itself be re- traumatizing, which isn’t well-captured in the positive evidence, because reasons for dropout and adverse events were often poorly or inconsistently reported. On the other hand, even when these trauma-memory approaches “work,” they are working against the body’s understanding of things by creating new cognitive-behavioral patterns that suppress the old conditioned fear responses as they come up. That can produce a reduction of symptoms without solving the root of them, in the same way that disciplining a child can force proper behavior without making it natural.

#### P25 — Somatic Experiencing / window of tolerance

SHA-256: `368d1d37b4df8ccdfa3ee7497e6fc21c748f0b5d0d76d2c63e17ef2a56cbf0a9`

The usual therapy theory here talks about expanding your “window of tolerance,” but I think my analogy is a better representation of what Levine is trying to say. He uses the concepts of titration (going from the shallow end of the pool slowly deeper), pendulation (going in and out of the deep end to learn safety there), and orientation (coming out of the pool, drying off, noticing you’re safe). That’s the beautiful thing about not actually being in the trauma. Since it’s a memory, you can approach it in an optimal and safe way, bit by bit.

#### P34 — Trauma-sensitive / restorative yoga

SHA-256: `e3d914ab1018593a63b8929d685bb34399119148fa7b79be298989e32426d955`

Trauma-Sensitive / Restorative Yoga After calming down with the breathwork and learning to listen to your body with SE, yoga can help the body-mind connection become more of a two-way conversation, which is more useful in the real world also. After all, we need to move in healthy ways and use our body as well as listen to it. We need to stretch, to have good posture, and to move the energy purposefully in our body so that we are able to meditate (which was the original point of yogic posture training).

#### P66 — Layer 4 / targeted memory work framing

SHA-256: `f82f53d8feda659a8ce9c62477c5fd4a62b56831ce0da4a64801020b85e579b2`

This is the part of the map I think of as targeted memory work or “reconsolidation,” which refers to the way we untangle the charged memory, reprocess its significance, and put it back together in a healthier way, while still being honest about what happened. It works best when you are having flashbacks to a specific event, rather than something more general that brainspotting or other prior therapies could touch with a broader brush. The goal here is to reduce the “stickiness” of these memories, so that we don’t get stuck every time they pop up.

#### P67 — EMDR mechanism

SHA-256: `683a0736dcfd9b957f6c84345bff3a7f37b376c86a939bc12da5c7ec81f8e476`

EMDR is the main modality designed exactly for reducing the charge held by specific traumatic events, like accidents, assaults, fights to the death, and so forth. Although it’s not completely understood how it works, the best theory is that by moving the eyes from side to side (or doing some other type of bilateral stimulation), you can split your attention, which weakens the durability of the memory you’re focusing on. In that more flexible state, you can re-encode a positive image (like, “I can handle this.”) onto the event before memory hardens again.

#### P70 — Hypnosis / EMDR comparison

SHA-256: `ad0e5f7263d31f71b983d38f6ac41323231c31913703289d750d0b8406f11374`

It’s interesting that EMDR used to be critiqued as a re-branded, minimal distillation of hypnosis. Even when you look at moving the eyes back and forth, that’s almost the classic hypnotic induction. That’s not to say that EMDR is hypnosis or it requires suggestibility, but the idea of splitting your attention is also similar. In hypnosis we use attention splitting to subdue the conscious mind and allow access to the lower-level programming layer in the subconscious.

#### P75 — Narrative and cognitive integration

SHA-256: `6d15d47ed3b3e1b859eafee07dbc76fb1d15b23f28b08e457b80c4bdf0dc0c7e`

Narrative and Cognitive Integration Once we’ve tuned into our body, our subconscious, and moved the energy in the ways it needed to move, there’s still the cognitive integration layer, because we’re actually humans, not just animals. This is the part that insurance often does pay for to start with (Cognitive Behavioral Therapy, etc.), although this guide is predicated on the idea that it’s not always the best place to start.

#### P88 — Outcomes / choosing therapies

SHA-256: `52294c3bd1294b3fed817f386a70851adff509b7aa3208c7aa2a8a93599fe8f7`

It is good to do some research before jumping into a long course of therapy, especially if it will cost a lot in time or money. But even if you have a zillion studies saying this therapy has a large effect size on the thing you’re treating, it’s still interesting to talk to people who’ve done these therapies and see how they were before vs after. It’s still important to see if they make some kind of sense, and finally, you still have to dip your feet in and see if it’s a fit for you.

## 4. Consequence for the humanization model

Do **not** optimize by mechanically deleting every risky-looking structure. That would erase legitimate Human prose and can over-constrain the writer.

Instead, track two things at once:

1. **Risk burden** — polished relationship-announcement, compressed abstraction, stacked closure, equalized explanatory packaging, or other operators supported by controlled detector evidence.
2. **Human-shape support** — concrete lived anchors, owned judgment, idiosyncratic wording, uneven realization, direct action/sensory detail, ordinary practical distinctions, and other locally observed features that keep prose from becoming a pure editorial package.

The relevant warning condition is **accumulation without compensation**: several risk-bearing operations stack in one local unit while concrete/owned/idiosyncratic realization thins out.

The controlled minimal pairs remain the best evidence for which edits move risk. The manual positive control is best used to study how otherwise-risky structures can coexist with Human verdicts.

## 5. Independence boundary

This is not a blind Pangram model. The current conversation already knows several labels, and the nine manual candidates were chosen after the owner reported all manual paragraphs Human.

A real predictive validation would require a fresh context or a pre-frozen rubric applied to unlabeled passages before detector labels are revealed.

## 6. Production implication

For manual humanization, prefer **surgical removal or re-realization of model-added risk operators** over global anti-pattern rules. Preserve legitimate authorial structure when it is supported by concrete, owned, or idiosyncratic realization.

Pangram remains downstream evidence. No new detector call was made for this record.

## 7. Provenance / transport

Owner correction received 2026-09-14. Temporary durable GitHub receipt: Pangram Humanization Lab issue #146.

Connected contents writes are currently unreliable/blocked for this content. This file is frozen for ordinary authenticated Git materialization and later read-back verification. The superseded earlier recovery package must not be used.
