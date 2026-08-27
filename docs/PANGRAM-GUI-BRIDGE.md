# Pangram persistent local GUI bridge

The bridge lets an authorized Chat enqueue a fixed-data request in GitHub and receive durable Pangram GUI evidence without opening a separate Work task or asking Joel to run a terminal command. The actual detector transport remains the existing **headed local Playwright → Brave → pangram.com** runner with Joel's dedicated persistent profile.

The bridge is deliberately not an editorial agent. It never rewrites prose, runs request-supplied commands, evaluates request-supplied code, accepts browser state, or substitutes an API detector.

## Fixed topology

- Tooling/result repository: `u-dont-existDOTcom/pangram-humanization-lab`
- Fixed code/result branch: `agent/pangram-local-playwright-gpt-20260818`
- Append-only request branch: `automation/pangram-gui-bridge-queue`
- Request path: `state/pangram-gui-bridge/requests/<lowercase-uuidv4>.json`
- Result path: `state/pangram-gui-bridge/results/<same-uuidv4>.json`
- Work/claim path: `state/pangram-gui-bridge/work/<same-uuidv4>.json`
- Durable duplicate claim: `state/pangram-gui-bridge/seen/<same-uuidv4>.json`
- Global paid intent: `state/pangram-gui-bridge/paid-reservations/<text-sha256>.json`
- Queue cursor: `state/pangram-gui-bridge/queue-cursor.json`
- Existing measurement evidence: `state/gui-runs/pangram-4/<text-sha256>/`
- Local service: `pangram-gui-bridge.service`

The separate branches avoid a two-writer race: Chat only appends request files to the queue branch; the desktop daemon alone advances the code/result branch. The daemon rejects queue rewrites, deletions, modifications, renames, nested request paths, or changes outside the request directory.

## Exact request schema

JSON is UTF-8 without a BOM, duplicate keys, non-finite numbers, control characters, or unknown fields. The maximum request size is 32 KiB. `request_id` must be a lowercase UUIDv4 and must exactly match the filename.

Read-only authentication verification has exactly three fields:

```json
{
  "schema_version": 1,
  "request_id": "<lowercase-uuidv4>",
  "operation": "verify"
}
```

`recover` and `localize` use this exact shape:

```json
{
  "schema_version": 1,
  "request_id": "<lowercase-uuidv4>",
  "operation": "recover",
  "source": {
    "repository": "u-dont-existDOTcom/joel-articles",
    "ref": "refs/heads/<trusted-source-branch>",
    "commit": "<lowercase-40-character-commit-sha>",
    "path": "articles/<trusted-markdown-path>.md",
    "file_sha256": "<exact-source-file-sha256>",
    "text_sha256": "<exact-reader-visible-text-sha256>",
    "text_word_count": 3548
  },
  "extraction_profile": "joel_articles_markdown_from_unique_introduction_v1",
  "audit_id": "<bounded-id>",
  "section_id": "<bounded-id>"
}
```

`localize` changes only `operation`. `measure` uses the same fields and adds:

```json
"call_cap": 1
```

`call_cap` is an integer from 1 through the repository maximum of 6. Only `measure` can reach a detector click. The supported operation semantics are:

- `verify`: launch headed Brave, verify the hydrated authenticated detector input, fill nothing, and submit nothing.
- `recover`: reuse a strong exact cache hit; otherwise perform read-only exact History recovery. Never click the detector.
- `localize`: reuse/recover the exact result and publish score-time localization evidence. Never click the detector.
- `measure`: reuse a strong cache first; recover before repeat when a GUI reservation, ambiguous failure, or durable paid-call reservation exists; only then permit one new guarded local GUI measurement.

The fixed source registry currently permits only `u-dont-existDOTcom/joel-articles` paths below `articles/`, a fully qualified `refs/heads/...` ref, and a commit that is the ref tip or its ancestor. Every exact path component is checked through the Git tree, and the final entry must be a regular blob rather than a symlink or submodule. File SHA, extracted-text SHA, and word count must all match before browser work.

## Named reader-visible extraction

`joel_articles_markdown_from_unique_introduction_v1` is code-owned and cannot be supplied or changed by a request. It:

1. requires exactly one `# Introduction` and starts there;
2. retains visible heading and list text while removing their Markdown markers;
3. replaces Markdown links with their visible labels and discards destinations;
4. removes the bold and inline-code markers present in the certified Somatic r15 extraction while preserving the exact historical treatment of single-emphasis spans;
5. excludes native/editor `**[EXISTING ...]**` placeholder lines;
6. excludes non-prose thematic dividers; and
7. collapses consecutive blank lines and terminates the exact text with one newline.

Remaining links, URLs, heading markers, or list markers fail closed. Most importantly, the request's exact extracted-text SHA and word count must match the fixed profile output, so new syntax or source drift cannot cross the browser boundary unnoticed. Requests cannot include extraction code, selectors, shell fragments, browser paths, profile paths, URLs, credentials, or arbitrary runner arguments.

## Enqueue from Chat

Chat should create exactly one new JSON file with the schema above on branch `automation/pangram-gui-bridge-queue`, at:

`state/pangram-gui-bridge/requests/<request_id>.json`

Use the connected GitHub file-creation capability, not a force push and not an update to an existing file. Never reuse a request id. The daemon polls the immutable branch, validates the entire append-only change set, durably claims the request, executes the fixed operation, and publishes the matching result on `agent/pangram-local-playwright-gpt-20260818`.

Chat then reads:

`state/pangram-gui-bridge/results/<request_id>.json`

The result records the queue commit and request hash; status/outcome; exact source and reader-visible identity; exact `response.overall` score; exact stored-History binding without the private History identifier; report-body, report-PDF, result, and localization paths/hashes; whether the request submitted; and any explicit `blocked` or `ambiguity` state.

## Cache, ambiguity, and durability contract

A cache hit is accepted only when all of these match: local Playwright transport, Pangram 4/4.0, `STAGE_SUCCESS`, exact source provenance, input SHA and word count, `stored_history_structured_result`, field path `response.overall`, exact UTF-8 History identity, and existing report body/PDF with matching hashes.

Before a new measure, the bridge durably creates a content-addressed global paid intent and an audit ledger reservation. The bridge treats either of those, any GUI reservation, any failure marked `detector_submission_attempted: true`, or a matching reservation found in **any** audit ledger as “action may have happened.” It runs read-only exact History recovery before any possible repeat. Ambiguous recovery is time-bound to the durable reservation and requires one unique exact History match; an older or multiply matching record cannot clear the guard. Failed recovery publishes `status: ambiguous` and `recover_before_repeat_required: true`; it does not submit again.

Paid-call reservations report whether they were newly created; an existing reservation routes to recovery rather than allowing another click. When an audit ledger already exists, cache-hit accounting is restart-idempotent by bridge request id; a read-only request never creates a new ledger or invents a future paid-call cap. Claims, work status, results, localization, cache events, reservations, and the cursor are path-scoped commits pushed through the existing `GitSync` contract. Ordinary remote-only `state/` descendants may be fast-forwarded. Runtime-affecting remote changes and true two-sided divergence remain fail-closed.

No cookie, password, token, browser storage, profile byte, raw History record, private History UUID, or private History URL is committed to the request or result store.

## Desktop installation and operation

The checked-in unit runs from Joel's existing installation and virtual environment:

`/mnt/hdd/home/joel/Téléchargements/pangram-local-runner-20260818`

Install the unit as `~/.config/systemd/user/pangram-gui-bridge.service`, then reload and enable it under `graphical-session.target`. The user manager supplies the live `DISPLAY`, `WAYLAND_DISPLAY`, `XDG_RUNTIME_DIR`, D-Bus, keyring, and SSH-agent environment; the unit must not hardcode session-specific values. It has `UMask=0077`, restarts on failure, and stops with the graphical session even though user lingering is enabled.

Read-only operator checks:

```bash
systemctl --user status pangram-gui-bridge.service
journalctl --user -u pangram-gui-bridge.service --since today
```

The daemon can be polled once for diagnosis from the installed repository with:

```bash
.venv/bin/python -m pangram_lab.gui_bridge once
```

Do not run a second copy while the service is active; a user-cache file lock rejects concurrent workers.

## Recovery

- Same request bytes after a daemon restart: return the existing durable result without re-execution.
- Durable claim but no result: resume processing the same immutable request.
- `failed` or `ambiguous` result: keep the cursor behind the request and safely reconcile/retry it; completed/invalid/ordinary blocked results are terminal and remotely re-confirmed after restart.
- Different bytes for an existing request id: publish a duplicate conflict and do not execute.
- Rewritten/diverged queue branch: stop queue processing until the topology is audited.
- Runtime change on result branch: update the installed checkout and restart the service; never hot-reload it beneath the running process.
- State-only result-branch advance: allow the existing guarded fast-forward and continue.
- Ambiguous measurement: issue `recover` or `localize` for the exact same input; never bypass with force or another transport.
