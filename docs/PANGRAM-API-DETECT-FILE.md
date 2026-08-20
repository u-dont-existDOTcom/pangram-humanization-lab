# Pangram single-file API measurement

Use `pangram-lab detect-file` when one exact reader-visible text boundary needs a programmatic Pangram-4 measurement. This is the normal API route for a single frozen candidate; use `pangram-local` only when GUI/History recovery or visual evidence is specifically useful.

## Safety contract

The command reuses the repository's existing `PangramClient`, `PangramCache`, and `GitSync` machinery. It therefore inherits:

- explicit `pangram-4` submission and expected version `4.0`;
- exact content-addressed cache identity;
- resume of a checkpointed task without a second POST;
- no automatic POST retry after an ambiguous submit;
- durable Git sync after pending-task checkpoint and completed result;
- auth probing before any billable POST;
- exact-input SHA-256 gate before credential access or detector work.

The current `PangramCache` stores the exact detector text. Because this repository is public, `detect-file` refuses to proceed unless `--allow-public-cache` is supplied. Use that flag only when the exact detector boundary is already public-safe. Private/unpublished inputs need a different cache/durability design; do not bypass this guard merely to get a detector result.

The command does not replace the six-paid-call section budget, stable audit/section identity, reader-visible representation gate, or article-wide semantic/fidelity checks in `CHATGPT-OPERATING-GUIDE.md`.

## Command

```bash
pangram-lab detect-file path/to/candidate.txt \
  --expect-sha <exact-64-character-sha256> \
  --measurement-key <stable-measurement-id> \
  --allow-public-cache
```

Credentials are read from `PANGRAM_API_KEY`; if absent, the CLI prompts invisibly and never saves the key.

For a self-hosted or alternate API endpoint, set `PANGRAM_BASE_URL` or pass `--base-url`:

```bash
PANGRAM_BASE_URL="https://your-endpoint.example" \
  pangram-lab detect-file candidate.txt \
  --expect-sha <sha256> \
  --measurement-key <stable-id> \
  --allow-public-cache
```

Do not put credentials in the URL, command line, Git files, or shell tracing.

## Evidence

A successful or pending measurement lives under:

```text
cache/pangram-4/4.0/<text-sha256>/<measurement-key>.json
```

That record contains the exact text, task identity, submitted model, status, and terminal result. A successful command also prints a compact receipt with the exact input hash, word count, measurement key, cache path, model/version gate, cache status, and detector result.

If the exact text/key already has a successful cache record, the command is a cache hit and makes no paid POST. If it has a pending task ID, the command resumes polling that task. If the prior submit is marked ambiguous, it fails closed rather than buying another call.

## Git durability

For normal paid article work, run on a named evidence branch with a configured `origin`. Do not use `--no-github`: the preflight, task checkpoint, and terminal result should be durable before another paid action.

Code-only CI must never invoke `detect-file` with real credentials or spend Pangram credits.
