# Pangram Humanization Lab v2 — Design

## Goal
Reuse the proven persistence/evidence behavior of Joel's earlier Pangram autopilot while adding adaptive Codex-designed detector experiments, live observability, Pangram-4 content-addressed caching/resume, and automatic private GitHub backup.

## Architecture
The lab is a new repository so the old working autopilot and Romance article remain untouched. `legacy_import.py` ingests successful Pangram-4 evidence from both old campaign states/raw files and the failed newer harness. `PangramCache` stores each exact text/model/version/measurement identity atomically. `PangramClient` checkpoints a task ID before polling and never automatically repeats an ambiguous POST. `CodexRunner` streams the designer/reviewer/analyst subprocess output live. `Engine` freezes design and blind editorial review before new Pangram calls, runs cached/base measurements and only preregistered exact repeats, computes deterministic contrasts/factor effects, then lets Codex decide whether another bounded experiment is informative.

## GitHub invariant
A private GitHub repository is established before detector work. Every durable experimental transition is committed/pushed. Files are saved locally before push; a push failure blocks subsequent paid detector submissions. Secrets are excluded.

## Planner contract
No `factor_bits`. Binary factor assignments are structured objects. `AI_ENDPOINT` and `HUMAN_ENDPOINT` are explicit exact-text probes. Contrasts reference literal probe IDs only. Derived means/interactions are computed deterministically and never masquerade as probe IDs.
