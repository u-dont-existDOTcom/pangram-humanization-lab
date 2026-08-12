# Pangram Humanization Lab v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a resumable adaptive Pangram-4 experiment lab on the earlier autopilot's persistence model.

**Architecture:** Content-addressed JSON cache + task-id checkpointing; streaming Codex subprocess adapter; strict explicit probe/factor schema; legacy evidence importer; deterministic experiment orchestration; private GitHub checkpoint after every durable event.

**Tech Stack:** Python standard library, pytest for development, Codex CLI, Pangram 4 asynchronous API, git + GitHub CLI.

## Tasks
- [x] Content-addressed Pangram cache with base/repeat identities.
- [x] Pangram-4 task checkpoint/resume and ambiguous-submit guard.
- [x] Legacy campaign/new-harness Pangram-4 result import.
- [x] Live role-prefixed Codex streaming with heartbeat and key isolation.
- [x] Strict current-Codex JSON schemas and non-brittle plan validation.
- [x] Blind reviewer → Pangram → repeats → deterministic stats → analyst loop.
- [x] Failure artifacts persisted before local validation can abort a run.
- [x] Private GitHub initialization and automatic state commits/pushes.
- [x] One-command Zorin installer and old-endpoint auto-discovery.
- [ ] Target-machine live Codex/Pangram/GitHub acceptance run.
