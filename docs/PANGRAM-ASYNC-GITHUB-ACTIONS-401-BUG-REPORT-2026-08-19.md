# Pangram support report: Pangram 4 async endpoint returns 401 only from GitHub-hosted Actions

Date: 2026-08-19

## Summary

The same Pangram API credential is accepted from a local Linux machine and from GitHub-hosted Actions against Pangram's V3 endpoint, but Pangram 4's async endpoint rejects requests originating from GitHub-hosted Actions with HTTP 401 `Invalid API key`.

This appears specific to `https://text.external-api.pangram.com/task` (and `/models`) from GitHub-hosted/Azure runner egress, rather than an invalid/missing key.

## Expected behavior

A valid API key that successfully runs Pangram 4 from a local machine should also authenticate when the same request is sent from a server/cloud CI runner, unless Pangram 4 has an origin/IP restriction or separate key policy that needs to be configured.

## Local Pangram 4 success

From a Zorin Linux machine, this request shape succeeds:

```http
POST https://text.external-api.pangram.com/task
x-api-key: <same key>
Content-Type: application/json
Accept: application/json
```

```json
{
  "text": "<60-word test text>",
  "public_dashboard_link": false,
  "model": "pangram-4"
}
```

The POST returns a task ID. Polling `GET /task/<task-id>` reaches `STAGE_SUCCESS` and returns:

```json
{
  "stage": "STAGE_SUCCESS",
  "version": "4.0",
  "prediction_short": "AI",
  "fraction_ai": 1.0
}
```

So the account has usable paid credits and the credential is authorized for Pangram 4 from this origin.

## GitHub-hosted Actions failure

The equivalent Pangram 4 POST from a GitHub-hosted Ubuntu runner fails before any task ID is issued:

```text
HTTP 401
{"detail":"Invalid API key"}
```

A durable failure record was written at approximately `2026-08-19T04:51:01.554Z`.

The runner receives `PANGRAM_API_KEY` from GitHub Actions secrets. Safe diagnostics show:

```text
KEY_NONEMPTY=True
HAS_EDGE_WHITESPACE=False
KEY_LENGTH=76
TRIMMED_LENGTH=76
```

No key contents or key hash were logged.

## Control proving that the GitHub Actions secret itself is accepted

From GitHub-hosted Actions, using the same repository secret, an intentionally malformed request to the documented V3 endpoint was sent with an empty JSON body:

```http
POST https://text.api.pangram.com/v3
x-api-key: <same GitHub Actions secret>
Content-Type: application/json

{}
```

At `2026-08-19T04:59:20Z` it returned:

```text
HTTP 400
{"error":"Missing 'text' in request body."}
```

A second run at `2026-08-19T05:00:05Z` returned the same HTTP 400 response.

That control is important: authentication passed far enough for Pangram to validate the body, so this is not explained by an empty secret, edge whitespace, or a generally invalid credential.

The V3 endpoint returns detector version `3.3.2` for paid detection, so it is not a substitute for the Pangram 4 async endpoint in this integration.

## Additional async-origin observation

From GitHub-hosted Actions, a non-billable request to:

```text
GET https://text.external-api.pangram.com/models
```

with the same `x-api-key` also returned HTTP 401.

## Reproduction matrix

| Origin | Endpoint | Result |
|---|---|---|
| Zorin Linux / local network | `POST text.external-api.pangram.com/task`, `model=pangram-4` | Success; task reaches `STAGE_SUCCESS`, version `4.0` |
| GitHub-hosted Actions / Azure | `POST text.api.pangram.com/v3` with `{}` | HTTP 400 `Missing 'text'`; credential accepted |
| GitHub-hosted Actions / Azure | `GET text.external-api.pangram.com/models` | HTTP 401 |
| GitHub-hosted Actions / Azure | `POST text.external-api.pangram.com/task`, `model=pangram-4` | HTTP 401 `Invalid API key`; no task ID |

## Questions for Pangram

1. Does `text.external-api.pangram.com` have an IP allowlist, cloud-provider/WAF restriction, geo restriction, or other origin policy that differs from `text.api.pangram.com/v3`?
2. Are GitHub-hosted Actions/Azure egress ranges intentionally blocked by the Pangram 4 async service?
3. Does the Pangram 4 async endpoint require a different API key type, account flag, or server-side allowlisting even when the same key works from a local client?
4. Is there a currently supported Pangram 4 endpoint intended for CI/server workloads that we should use instead?
5. If this is unintended, can you check the authentication/WAF logs around `2026-08-19T04:51:01Z` and explain why this request was classified as `Invalid API key`?

We can provide additional request timestamps or non-secret diagnostics if useful. We will not send the API key by email.
