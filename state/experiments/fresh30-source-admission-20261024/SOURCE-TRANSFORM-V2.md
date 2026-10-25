# Alternative baseline architecture — controlled source transformation

**Predeclared 2026-10-24; method V2 not yet executed at filing.**

## Why V1 was stopped
Three separate Claude Sonnet draft generations received only current-chat-derived meaning bullets rather than the source paragraph. Their independently invoked source readers found meaning discrepancies in all three. The source-dossier approach was stopped **without A/B writer outputs or Pangram**. See `FAILED-DOSSIER-PILOT.json` for all three inputs/outcomes. The fidelity critic also treated some synonymous wording shifts as errors; preserve that limitation separately from genuine missing/additional claims.

This was a **failure of baseline construction/admission**, not evidence that literal examples cannot improve humanization.

## Different architecture V2
For the same frozen three source families (T05, T09, T13), a fresh baseline generator sees the actual exact registered paragraph and is asked to render a compact, clear **model-authored** version while preserving its claims, certainty, personal voice, imagery and rhetorical functions. This is a controlled reverse transformation, not content reconstruction from an incomplete bullet outline. The reference paragraph is never shown to A/B repair writers. Both receive the same admitted model baseline plus the same protected-function dossier; Arm B also receives its predeclared literal teaching example from another article.

The fidelity reviewer has a genuinely fresh context and must count only **material** omissions/additions/certainty/agency/function differences, not automatic word-level dissimilarity. A baseline failing that gate is recorded as failed and is not repeatedly patched to force a pass. No variant is silently replaced after an outcome.

## Fixed controls
- Model: Claude Sonnet; medium effort; no tools, no session persistence, no settings or hooks; one first attempt per stage.
- Cases: T05 (medium teacher match), T09 (weak), T13 (strong), chosen before any V1 or V2 results.
- A/B order: T05 A then B; T09 B then A; T13 A then B.
- Separate fresh CLI invocations for baseline, baseline fidelity, A, B and blinded-to-arm editorial comparison.
- The reviewer observes source and anonymous candidates, not the teacher evidence or Pangram. This is independently invoked *context*, not an independent provider or owner approval.
- No paid detector calls in smoke. Only faithful, decision-relevant successful first attempts could later justify individual Pangram calls of 1–3 paragraphs.
- Full prompt and stdout are retained under separate `PILOT-SOURCE-RESULTS/` identities; V1 output is never overwritten.

The V2 source-controlled experiment may still fail because prose processing damages meaning or models reproduce the same underlying cadence. If it fails, stop rather than add a larger prohibition stack; consider deterministic editorial minimal-dose or a fixed candidate pool with a separate selector.

## Status
FROZEN DESIGN. Execution and validation are reported only after actual fresh CLI jobs and exact source hashes are bound. Never conflate a new source-controlled model draft with owner-authored prose.
