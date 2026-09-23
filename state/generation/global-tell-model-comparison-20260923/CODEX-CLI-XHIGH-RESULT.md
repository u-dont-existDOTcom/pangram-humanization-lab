# Codex subscription-CLI global tell-ledger benchmark

Date: 2026-09-23
Status: BOUNDED PROVIDER-NATIVE-CLI EVIDENCE / SAME FROZEN SIX-CASE BENCHMARK / NO PANGRAM CALLS

## Purpose

Test whether the local authenticated Codex subscription CLI changes GPT-6 Sol/Astra performance enough to affect the global tell-ledger routing decision.

This uses the same six frozen passages, twelve owner/editorially grounded scored cells, and tell definitions as the OpenRouter/Venice comparisons.

## Isolation / route

Each case used a fresh local Codex CLI process with:
- neutral `/tmp` workspace;
- `--ignore-user-config`;
- `--ignore-rules`;
- `--ephemeral`;
- read-only sandbox;
- structured output schema;
- prompt explicitly prohibiting tools/environment inspection;
- no resumed session;
- `model_reasoning_effort="xhigh"`.

No OpenRouter/Venice API call was used for these GPT runs.

## Results

### GPT-6 Sol xhigh via Codex CLI

- **9/12 exact**
- 1 UNCERTAIN
- **2 wrong-polarity calls**
- wrong cells:
  - known-Human direct-advice cadence: expected T02 ABSENT -> PRESENT;
  - known-Human seat-belt cadence: expected T02 ABSENT -> PRESENT.
- RT2 T04 scene-skinned staircase: UNCERTAIN.

Compared with GPT-6 Sol max via Venice (8/12, 3 wrong polarity), the local CLI route improved this bounded sample somewhat but did not eliminate unsafe confident errors.

### GPT-6 Astra xhigh via Codex CLI

- **8/12 exact**
- 1 UNCERTAIN
- **3 wrong-polarity calls**
- wrong cells:
  - dangerous-adult abrupt complication: expected T03 PRESENT -> ABSENT;
  - known-Human direct-advice cadence: expected T02 ABSENT -> PRESENT;
  - known-Human seat-belt cadence: expected T02 ABSENT -> PRESENT.
- RT2 T04 scene-skinned staircase: UNCERTAIN.

Astra CLI therefore does not outperform Sol CLI on this tell-ledger task.

## Interpretation

Provider-native CLI use is the correct default route when authenticated/capability-equivalent because it avoids metered API spend. But **route economy does not make GPT a safe clearing judge**.

Current bounded model evidence:
- Opus remains the stronger global tell-ledger candidate;
- Sol CLI can be a secondary/advisory cross-check;
- Astra CLI does not currently add value over Sol CLI for this task;
- GPT PRESENT/ABSENT results must not override owner/editorial truth or a stronger calibrated Opus/narrow-audit result.

The provider surface matters: Sol xhigh CLI and Sol max Venice do not produce identical behavior. Do not transfer an API benchmark mechanically to a CLI route.

## Next boundary

Claude Code CLI exists and exposes low/medium/high/xhigh/max, but its local OAuth session was expired during this benchmark. Claude CLI effort/model calibration therefore remains pending a human re-login.

Do not use the OpenRouter Opus effort ladder as proof of Claude-CLI effort requirements.

No Pangram calls were used.
