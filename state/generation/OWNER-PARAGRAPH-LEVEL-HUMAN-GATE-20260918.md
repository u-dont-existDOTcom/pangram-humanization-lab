# Owner calibration — paragraph-level Human gate

Date: 2026-09-18
Status: **ACTIVE OWNER PRODUCTION RULE**

## Owner instruction

Do not treat a full-section Pangram pass as sufficient.

When paragraph-level testing is possible:
- each paragraph should independently test Human before the section is treated as detector-clean;
- passing paragraphs should be left alone rather than continually polished;
- whole-boundary Human results cannot mask a paragraph that independently reads AI.

## Editorial nuance

Joel accepts that some compression/model shape can remain inside genuine Human prose and genuine Human experience when the paragraph itself still reads/tests Human.

The target remains less compressed and less polished than the model's default, but detector-clean paragraphs do not need gratuitous rewriting.

## Short-text boundary

Do not pad, duplicate, merge, or surround a short paragraph with known-Human anchor prose solely to force an individual detector result.

If the current Pangram surface will not measure the paragraph independently:
- mark it as unmeasured;
- rely on owner/editorial judgment;
- use another valid short-text route only if explicitly available/authorized;
- never promote a contextual/anchored pass into an individual paragraph claim.

## Production consequence

Evidence hierarchy for a paragraph:
1. owner/editorial judgment;
2. independent paragraph detector result when technically valid;
3. integrated-boundary result as secondary context only;
4. preservation/fidelity throughout.