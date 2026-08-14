# Pangram Humanization Lab agent map

## Authority

1. Current owner and task requirements
2. `state/LESSON-INDEX.md` for the current lesson read order and branch routing
3. `docs/INDEX.md` for experiments, closeout, Actions, and release evidence
4. Current case artifacts, tests, cache/state records, and Git history
5. Relevant current patterns from `u-dont-existDOTcom/universal-dev-architecture`

Do not rely on remembered phrase rules or stale bundles.

## Validation

- Install test environment: `python -m pip install -e '.[test]'`
- Complete deterministic gate: `python -m pytest -q`
- Lesson audit: `PYTHONPATH=src python -m pangram_lab.lesson_closeout audit --ref HEAD`
- Changed-range closeout: `PYTHONPATH=src python -m pangram_lab.lesson_closeout check --base <base> --head HEAD`
- Local one-command run: `./INSTALL-AND-RUN.sh`

Live Pangram calls require the established cache/checkpoint path and must never substitute for deterministic tests.

## Workflow

Use an isolated task branch/worktree and a pull request. For substantive editorial, detector, experiment, reconstruction, or automation work, run lesson closeout before reporting completion. Record each finding as promoted, provisional, project-specific, superseded, or no-new-lesson, with exact evidence. Update the current recovery checkpoint at durable boundaries.

## Branch roles

- `main`: canonical code, current lessons, and project state
- `automation/pangram-fixed-batch`: long-lived exact experiment evidence referenced by the lesson index
- task branches: proposed code, experiment, lesson, or documentation changes

## Safety

Never print or commit the Pangram key. Preserve task IDs and ambiguous transport failures; do not automatically buy a duplicate detector call. Do not let an installer or stale package overwrite newer canonical Git state.

## Code review rules

- Human/editorial judgment remains the authority; detector outcomes are evidence, not license to damage meaning, voice, or owner-final claims.
- Every substantive finding must be dispositioned and tied to exact evidence; changed evidence requires review again.
- Do not promote passage-specific detector quirks into universal phrase rules without transferable evidence and limits.

Treat chat as disposable working memory. A fresh worker must recover from Git without repeating completed work.
