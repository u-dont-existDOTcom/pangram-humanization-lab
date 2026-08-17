# Romance Concept-Flow Current State — 2026-08-17

## Authority recovered

- Working branch: `agent/romance-concept-flow-improvement-20260817`.
- Base head: `agent/romance-architecture-map-2026-08-16@4ac56a883f147a59a003c05c3387423399609f8b`.
- Base head message: `state: materialize current Romance master and visible boundary`.
- `joel-articles/main` remains a blocked governance incubator and explicitly says no verified canonical article is registered there. Private Romance prose therefore remains controlled by the Pangram-lab assembly/state chain plus current Joel corrections.

## Exact current materialized boundary before this pass

- Master: `work/romance-current-assembly/current-master.md`
- Source bytes: 106,955
- Source SHA-256: `99b9e429f83f2aac7f879fb97abfb3daf050d3211a4f0269fb1b2caa0ca70ce6`
- Reader-visible bytes: 104,668
- Reader-visible words: 18,268
- Reader-visible SHA-256: `25ce4bd4e5845884a5c8988ba88f87e2a5e2f469417402cf1cc9cc8b0594a3d2`
- Assembly operations: 23
- Latest materialized owner change: Aug. 17 `After leaving` correction adding self-contribution and ex-perspective/internal-conflict language.

## Architecture drift discovered at recovery

`work/romance-current-assembly/ARCHITECTURE.md` still indexes the immediately previous boundary:

- old source SHA: `dbbc02fde8330045a945a45d51b12d87ed386167958e7c9870852caf51c479ff`
- old reader-visible SHA: `fd47cad5825ab8f3bafd810c4c0b7e0a817edff40bd802edf66dac7247b6412e`
- old word count: 18,248

The prose authority is newer than the map. This is assembly/map drift to repair during the current pass; it is not permission to reinterpret article authority.

## Current detector evidence

### Whole-article manual GUI PDFs

Joel supplied Pangram 4.0 PDFs for the prior 18,248-word split boundary:

- Part 1: 11,506 words; 92.5% Human / 7.5% AI; High-confidence block segmentation.
- Part 2: 6,742 words; 98.9% Human / 1.1% AI; High-confidence block segmentation.

Those totals sum to 18,248 words and therefore correspond to the pre-Aug.-17 reader-visible boundary, not the current 18,268-word exact hash.

### Useful localized GUI evidence

- The Part 1 PDF isolates a 413-word High-confidence AI span crossing the current Talk section into Casual Sex; previous assistant rewrite attempts did not improve it reliably. Preserve current Talk/Casual unless a semantic defect independently appears.
- A 574-word Primal diagnostic PDF reports 54% AI / 46% Human and alternates concrete/lived green blocks with abstract/symmetrical red blocks. The tested text is diagnostic/candidate material, not automatically article authority.
- Part 2 isolates the short ordinary-life psychedelic sentence as AI in the old boundary; Joel reports a revised short paragraph as Human/Low confidence. Treat as provisional until tested in full context.
- Joel's Aug. 17 owner rewrite of the 201-word `After leaving` span is reported by the GUI as AI/High and as `paraphrased or rewritten`; owner/editorial improvement controls despite that label.

## API status

The repository-secret Pangram route currently fails at POST with HTTP 401 `Invalid API key`. Joel has contacted Pangram support about the new key. No new paid detector work should be attempted until the credential issue is resolved. Manual GUI/PDF inspection is the temporary detector path.

## Current task

Specification: `docs/superpowers/specs/2026-08-17-romance-concept-flow-improvement.md`
Plan: `docs/superpowers/plans/2026-08-17-romance-concept-flow-improvement.md`

Next step: complete the concept setup/primary-home/application audit before editing prose.