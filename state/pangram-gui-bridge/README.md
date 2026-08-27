# Pangram GUI bridge durable state

The persistent headed local GUI bridge is documented in `docs/PANGRAM-GUI-BRIDGE.md`.

- Append-only requests live on `automation/pangram-gui-bridge-queue` under `state/pangram-gui-bridge/requests/<uuidv4>.json`.
- Results, claims, work status, content-addressed paid intents, conflicts, and the queue cursor live on `agent/pangram-local-playwright-gpt-20260818` under this directory.
- Measurement evidence remains content-addressed under `state/gui-runs/pangram-4/<text-sha256>/`.

Never add secrets, cookies, browser-profile bytes, private History identifiers/URLs, raw History records, request-provided code, or mutable request files here.
