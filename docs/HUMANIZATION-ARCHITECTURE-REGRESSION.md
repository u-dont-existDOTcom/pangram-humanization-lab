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

## Authorship-signal regression after substantial rewriting

For D3 sectional reconstruction or D4 article-wide regeneration, also compare the authoritative original and candidate against a held-out, genre-relevant owner profile under `IDIOLECT-RETENTION-PROTOCOL.md`. This is not required after every typo fix or narrow local repair.

Keep the results separate:

- architecture/fidelity determines whether the prose is allowed to mean what it means;
- Pangram measures the exact reader-visible boundary under its detector;
- the idiolect-retention report measures movement relative to the selected author corpus under its named instrument.

A preserve-voice prompt is not validation, a Pangram pass does not prove Joel's authorship signal survived, and a profile-similarity increase does not prove the prose is faithful or good. Use no universal threshold. When substantial rewriting moves away from both measured profile channels, inspect the edit, restore owner wording or realization, reduce the edit dose, and localize the repair before manufacturing stylistic quirks.

## Spiritual Bypassing incident

The 2026-08-14 Spiritual Bypassing audit demonstrated the failure directly: a reader-visible full article reached 100% Human while its first section no longer fulfilled `A Primer on Spiritual Bypassing`. Four fresh model-written primer realizations then failed; the successful repair came from finding the existing owner mechanism article-wide and routing it into the primer. A later cold audit also restored an inherited line that detector-focused editing had silently dropped.

See `state/SPIRITUAL-BYPASSING-HUMANIZATION-ARCHITECTURE-INCIDENT-2026-08-14.md` for provenance and exact evidence routing.

<!-- verification-trigger-after-closeout -->
