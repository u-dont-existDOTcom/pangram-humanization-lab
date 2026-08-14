# Humanization architecture regression gate

Use this during every Joel article humanization task, including Pangram-required work.

## Blocking rule

Humanization does not suspend article-level editorial reasoning. Before the first detector call and **after every detector-driven edit**, run an **architecture regression** from the complete article, not from the latest detector window.

Check:

- article title vs section heading vs subheading identity;
- **heading promise** and whether the section actually fulfills it;
- **paragraph jobs** and whether each paragraph advances the thought;
- the reader's **live question** / curious-reader chain;
- actor → action → object, mechanism, chronology, and causality;
- protected rhetorical functions, claims, and owner-final language;
- **article-wide** duplication, misplaced evidence, and pre-completed reasoning;
- whether the needed thought already exists as an **owner realization** elsewhere before generating a new explanation or asking Joel for input;
- real stopping point;
- fidelity against the highest-authority baseline, including apparently inferable lines.

If a local red window is coherent in isolation, inspect placement and routing before paraphrasing it. A detector-red span may be the symptom of duplicate realization or wrong architecture rather than sentence-level style.

A **100% Human** result is not editorially acceptable when the architecture regression fails. Detector green cannot repair a section that no longer fulfills its heading, a broken paragraph chain, a lost protected function, or fidelity loss.

## Spiritual Bypassing incident

The 2026-08-14 Spiritual Bypassing audit demonstrated the failure directly: a reader-visible full article reached 100% Human while its first section no longer fulfilled `A Primer on Spiritual Bypassing`. Four fresh model-written primer realizations then failed; the successful repair came from finding the existing owner mechanism article-wide and routing it into the primer. A later cold audit also restored an inherited line that detector-focused editing had silently dropped.

See `state/SPIRITUAL-BYPASSING-HUMANIZATION-ARCHITECTURE-INCIDENT-2026-08-14.md` for provenance and exact evidence routing.

<!-- verification-trigger-after-closeout -->
