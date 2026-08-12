# Live smoke tests

Live smoke is deliberately **not** part of ordinary `pytest`; it may consume provider or detector quota and requires local CLI authentication/credentials.

Run from the installed project root:

```bash
python scripts/live_smoke.py --claude --codex --pangram --research --heartbeat
```

That checks Pangram model availability but does not submit text. Add `--pangram-submit` explicitly to spend one harmless detector task.

The report is written under `.state/live-smoke/` by default and redacts known detector/search secret values. Provider calls use the same `ProcessRunner` heartbeat and artifact storage as the main runtime.
