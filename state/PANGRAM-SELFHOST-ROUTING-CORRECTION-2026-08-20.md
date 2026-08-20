# Pangram self-hosted routing correction — 2026-08-20

Status: direct owner correction plus fresh live evidence. This routing note supersedes stale transport conclusions that conflict with it.

## Current normal route

For ordinary programmatic Pangram measurements, use the private trusted self-hosted executor:

- public research/evidence repository: `u-dont-existDOTcom/pangram-humanization-lab`
- canonical branch: `main`
- fixed-batch evidence branch: `automation/pangram-fixed-batch`
- private execution envelope: `u-dont-existDOTcom/pangram-private-executor`
- self-hosted runner labels: `[self-hosted, linux, x64, pangram]`

The private executor receives one immutable `requests/<request-id>.json`, verifies the referenced public fixed-batch spec and exact SHA-256, then runs the canonical fixed-batch machinery on the self-hosted runner. It does not expose the Pangram API key to ChatGPT or the public repository.

## Fresh live proof

Fresh uncached route test `pangram4-selfhost-route-retest-2026-08-20-a` completed on 2026-08-20 through the private self-hosted executor:

- Pangram version: `4.0`
- stage: `STAGE_SUCCESS`
- 60-word fresh input
- `paid_api_calls: 1`
- `cache_hits: 0`
- `estimated_credits: 1`
- `estimated_cost_usd: 0.05`
- result includes Pangram `windows` metadata

Exact public evidence lives on `automation/pangram-fixed-batch` in `state/experiments/pangram4-selfhost-route-retest-2026-08-20-a-results.json`. The private request is `u-dont-existDOTcom/pangram-private-executor:requests/pangram4-selfhost-route-retest-2026-08-20-a.json`.

## Error-source classification

Never infer Pangram account credit state from an unrelated transport failure.

- **Browserbase HTTP 402**: Browserbase browser-minute quota. It says nothing about Pangram account credits.
- **GitHub-hosted Actions -> `text.external-api.pangram.com` HTTP 401**: known origin-specific compatibility issue (#95). Do not re-debug the API key or use GitHub-hosted execution as the normal Pangram route.
- **Direct/standard Pangram endpoint failure from another execution environment**: classify that exact route only. It does not override a fresh successful self-hosted-executor result.
- **Self-hosted Pangram API HTTP 402**: only this supports a current conclusion that the Pangram account available to the trusted self-hosted route lacks credits.
- **repository section-call cap**: internal safety/cost governance, not Pangram account balance.

## Paid-run contract

For a new fixed-batch measurement:

1. Freeze the exact reader-visible text and stable audit/section identity.
2. Check completed cache/results, pending task IDs, ambiguous submissions, and section call ledger before any POST.
3. Commit the exact spec to `automation/pangram-fixed-batch` under `experiments/...json`.
4. Compute and verify the exact spec SHA-256.
5. Add exactly one immutable request file to private executor `main`:

```json
{
  "format": "pangram-private-executor-request-v1",
  "request_id": "<unique-id>",
  "public_repo": "u-dont-existDOTcom/pangram-humanization-lab",
  "public_branch": "automation/pangram-fixed-batch",
  "spec_path": "experiments/<spec>.json",
  "spec_sha256": "<exact lowercase sha256>",
  "confirmation": "RUN_PAID_PANGRAM_FIXED_BATCH"
}
```

6. Let the private executor dispatch the canonical runner on `[self-hosted, linux, x64, pangram]`.
7. Verify the committed result, exact text/hash, `STAGE_SUCCESS`, explicit `version: "4.0"`, call accounting, and result windows before another paid request.

Do not use Browserbase for ordinary measurements. Do not ask Joel to run routine Pangram commands manually when the private self-hosted route can execute the task. Do not create another infrastructure smoke test merely to prove the route.

## Existing safety invariants remain

- cache before POST;
- resume pending task rather than resubmitting;
- no automatic retry after ambiguous POST;
- no repeat of a completed exact measurement;
- explicit `model: pangram-4` and returned `version: "4.0"`;
- durable result/cache/ledger state before another paid request;
- six-call repair cap per stable audit/section unless owner authorization says otherwise;
- exact reader-visible boundary and article semantic/fidelity gates remain blocking.
