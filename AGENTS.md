# Evidence-branch agent map

## Authority

1. Current owner/task requirements
2. `state/CURRENT-STATE.md` on this branch
3. Exact result, cache, call-ledger, task-checkpoint, and Git history evidence
4. `state/LESSON-INBOX.json` for unresolved semantic review identities
5. Canonical lesson disposition on `main`

This branch is durable detector evidence. Never reconstruct it from chat or overwrite newer state with a stale bundle.

## Branch role

- `automation/pangram-fixed-batch`: long-lived exact evidence and the single manual paid runner
- `main`: canonical code, lesson ledger/index, and repository governance
- task branches: proposed evidence-workflow changes; never use them to reset call budgets

## Validation

- Bootstrap: `python -m pip install -e '.[test]'`
- Full test gate: `python -m pytest -q`
- Paid-dispatch tests: `python -m pytest -q tests/test_paid_dispatch.py`
- Repository audit: `python scripts/audit_codex_github.py --root . --fail-on error`
- Manual preflight: `python scripts/validate_paid_dispatch.py --spec <experiments/file.json> --out <canonical-result-or-empty> --confirmation RUN_PAID_PANGRAM_FIXED_BATCH`

## Paid-call safety

Push and pull-request events may run tests only. A detector job may run only from `workflow_dispatch` after the exact confirmation and path/accounting preflight pass. Never print or retrieve the Pangram key. Never dispatch while another detector task or branch write is active. Preserve task IDs, ambiguous POST state, exact text hashes, call-ledger reservations, cache hits, and the six-paid-call section cap.

Historic task workflows are non-executable provenance under `docs/workflow-archive/automation-pangram-fixed-batch/`. Do not move them back into `.github/workflows`.

Treat chat as disposable memory. Recover from current Git refs and Actions state before any detector action.
