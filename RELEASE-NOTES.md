# Pangram Humanization Lab v2 — Release Notes

This release replaces the failed standalone experiment-harness execution path with a new lab that preserves the earlier working Pangram autopilot's durable measurement model while adding adaptive controlled experiments.

## Relevant repairs

- Every successful Pangram-4 result is stored content-addressably by exact submitted-text hash and reused across reruns/cases.
- Pending Pangram task IDs are checkpointed before polling and resumed without another POST.
- Ambiguous POST failures (transport loss, 429, or 5xx before a task ID is received) are frozen and never automatically resubmitted.
- Existing live Pangram-4 successes are imported from the old campaign-state/raw-response format and the newer experiment-harness `state.json` format. Dry-run measurements are ignored.
- The current external async API contract uses `x-api-key`, a zero-task auth probe, POST `/task` with `text` + `public_dashboard_link`, and GET `/task/{task_id}`. The obsolete `/models` and request-time `model` path is not used.
- Codex is run with JSONL streaming. Agent progress messages, commands/tool status, phase boundaries, elapsed-time heartbeats, and final plan/review summaries are visible in the terminal; model chain-of-thought is not printed.
- The planner schema uses explicit factor assignments instead of `factor_bits`; contrast endpoints are literal probe IDs. Invalid plans are persisted and automatically sent back to Codex for up to three bounded repair attempts before the harness stops.
- Frozen `plan.json` and `review.json` artifacts are reused after interruption. Completed rounds recorded in `history.json` are skipped on restart.
- A separate private GitHub repository is established before detector work. Every task checkpoint, result, Codex artifact, failure, statistics file, and analysis is committed/pushed. A push failure blocks the next paid detector submission.

## First run

```bash
cd ~/Téléchargements
unzip -o pangram-humanization-lab-v2.zip
cd pangram-humanization-lab-v2
./INSTALL-AND-RUN.sh
```

The installer will reuse `AI.txt` and `HUMAN.txt` from the prior `pangram-experiment-harness-v1` directory if they are not already in this directory.
