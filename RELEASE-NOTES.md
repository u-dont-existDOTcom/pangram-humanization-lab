# Pangram Humanization Lab v2.0.1 — Release Notes

This is an in-place corrective release for the first v2 target-machine run.

## Root cause confirmed by live evidence

The v2 async client correctly switched authentication to `x-api-key`, but it also removed the request-time model selector. The resulting paid task completed successfully as Pangram `3.3.2`, proving that the async endpoint defaulted away from Pangram 4 when no model was specified. The earlier validated Pangram-4 harness explicitly sent `model: pangram-4` and received terminal `version: 4.0`.

## Repairs

- `POST /task` now includes `model: pangram-4` while retaining `x-api-key` authentication and the zero-task auth probe.
- The already-paid v2.0 task is not discarded: on restart, its saved task ID is polled, the complete `3.3.2` terminal response is archived, and GitHub sync completes before a corrected Pangram-4 POST.
- New pending/cache records persist `submitted_model`.
- If an explicit `pangram-4` request ever returns a non-4.0 terminal version, that response is archived and the harness fails closed without another automatic paid POST.
- Cache hits, pending tasks, ambiguous POSTs, completed rounds, frozen Codex artifacts, and GitHub durability behavior remain unchanged.

## In-place upgrade

Do not delete the existing folder; its `.git`, cache, cases, and task checkpoint are the evidence we need to preserve.

```bash
cd ~/Téléchargements
unzip -o pangram-humanization-lab-v2.0.1.zip
cd pangram-humanization-lab-v2
./INSTALL-AND-RUN.sh
```

The installer commits and pushes the patched source to the existing private `pangram-humanization-lab` GitHub repository before any new detector submission.
