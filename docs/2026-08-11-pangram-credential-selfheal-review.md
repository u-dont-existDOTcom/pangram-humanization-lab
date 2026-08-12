# Pangram credential + repair-planner completion review — 2026-08-11

## Evidence that triggered this repair

Target-machine evidence package: `AUTHORIAL-FLOW-EVIDENCE-bounded-failure-20260811-182825.zip`.

The captured installer live-smoke report established:

- Claude Code `claude-opus-5`: **pass**.
- Codex CLI `gpt-5.6-sol`: **pass**.
- Pangram `/models`: **401 Unauthorized**.
- The bootstrap controller correctly captured and redacted the full smoke report and entered repair diagnosis.
- The repair planner then failed before producing a plan because Codex CLI 0.147.0 rejected the `RepairPlan` output schema: root object missing `additionalProperties: false`.
- Its next configured fallback, `gpt-5.6`, is unsupported by Codex when authenticated through the ChatGPT account.

This means the evidence/package plumbing worked, but the repair planner itself could not execute, and a credential failure was incorrectly routed as code-repairable provider plumbing.

## Repairs in this release

1. `RepairPlan`, `ReviewDecision`, and the other Pydantic structured-output models used by Codex are now strict (`extra='forbid'`), which generates `additionalProperties: false` recursively for object schemas.
2. A recursive regression test covers developmental and research Pydantic schemas, including nested research evidence records.
3. The unsupported default Codex fallback `gpt-5.6` was removed. Defaults are `gpt-5.6-sol` followed by the Codex CLI default.
4. Pangram HTTP 401/403 during live smoke is explicitly classified as `PANGRAM_API_KEY` credential refresh, exit code 3, rather than a code-repair candidate.
5. Bootstrap preflight recognizes that credential result and does **not** invoke write-capable Codex for it.
6. `INSTALL-AND-RUN.sh` securely prompts once for a replacement Pangram key when a previously supplied key is rejected, exports it only for the current installer/runtime process, and reruns the exact live smoke. The replacement key is not persisted.
7. Runtime detector calls independently catch Pangram 401/403, invalidate the rejected in-process key/client, clear pending Pangram task identity, and retry. The lazy Pangram key provider then asks for a fresh key on the same resumed thread.

## Validation in build environment

- New causal regressions: pass.
- Focused repair/bootstrap/live-smoke/runtime/release/model-adapter suite: pass.
- Full suite before release freeze: 223 passed, 1 dependency-gated real-LangGraph module skip.
- The skipped module remains target-machine-only because LangGraph is not installed in this build container.

## Still pending target-machine verification

This exact new release still needs the Zorin acceptance run for:

- real LangGraph module under the new code;
- secure Pangram-key refresh prompt after the previously rejected credential;
- Pangram `/models` success with a valid replacement key;
- live repair-planner structured output with Codex CLI 0.147.0;
- automatic installer → existing-thread continuation after smoke passes.

No target-machine status from an earlier release is transferred to this exact commit except as historical evidence.
