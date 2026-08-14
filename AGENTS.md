# Evidence-branch agent map

## Authority

1. Current owner/task requirements
2. `state/CURRENT-STATE.md` on this branch
3. Exact result, cache, call-ledger, task-checkpoint, request, and Git history evidence
4. `state/LESSON-INBOX.json` for unresolved semantic review identities
5. Canonical lesson disposition on `main`

This branch is durable detector evidence. Never reconstruct it from chat or overwrite newer state with a stale bundle.

## Branch role

- `automation/pangram-fixed-batch`: long-lived exact evidence and the single guarded automatic paid runner
- `main`: canonical code, lesson ledger/index, and repository governance
- task branches: proposed evidence-workflow changes; never use them to reset call budgets

## Validation

- Bootstrap: `python -m pip install -e '.[test]'`
- Full test gate: `python -m pytest -q`
- Paid-request tests: `python -m pytest -q tests/test_paid_dispatch.py tests/test_paid_push.py tests/test_paid_workflow_security.py`
- Repository audit: `python scripts/audit_codex_github.py --root . --fail-on error`
- Push preflight: `python scripts/validate_paid_push.py --base <before-sha> --head <after-sha>`

## Paid-call safety

Ordinary push and pull-request events run tests only. A detector job may run only when a push to the exact evidence ref adds exactly one immutable `requests/pangram/<experiment-id>.json` file and its hash-bound new spec, with no bundled third change. The request must carry the exact paid confirmation and canonical experiment identity. Never print or retrieve the Pangram key. Never stage a paid request while another detector task or branch write is active. Preserve task IDs, ambiguous POST state, exact text hashes, call-ledger reservations, cache hits, and the six-paid-call section cap.

Historic task workflows are non-executable provenance under `docs/workflow-archive/automation-pangram-fixed-batch/`. Do not move them back into `.github/workflows`, and do not restore commit-message or task-specific paid triggers.

Treat chat as disposable memory. Recover from current Git refs and Actions state before any detector action.
