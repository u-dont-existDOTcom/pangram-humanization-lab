# Pangram local history-API binding — 2026-08-19

## Live owner-machine evidence

Two owner-machine recovery checkpoints matter:

1. The 181-test run exposed the current long-document report transport and API schema.
2. The latest 190-test run exercised the first literal stored-record matcher. It passed **190/190** deterministic tests, observed ten existing browser/report candidates, made **no repeat Part-1 detector submission**, made **no Part-2 detector submission**, and found **no byte-identical Part-1 string** in the stored history records it visited.

The 190-test result does not show that the paid Part-1 result is absent. It shows only that literal UTF-8 equality was too strict as the sole stored-record identity mechanism.

## Current long-document transport

The privacy-bounded diagnostic established:

- report page route: `https://www.pangram.com/history/<uuid>`;
- current page title: `Your AI Report | Pangram`;
- current long-document overview exposes summary controls such as `AI 8%` and `Human 92%` plus paginated highlight navigation;
- report data is loaded from `https://web.pangram.com/api/history/<uuid>/`;
- record keys include `prompt`, `response`, `response_payload`, `prediction`, `prediction_prob`, `model_id`, and `uuid`;
- list data comes from `https://web.pangram.com/api/history-list/`.

The diagnostic intentionally does not persist response bodies, cookies, session/storage values, request headers, query strings, or private result UUIDs/URLs.

The observed 92% Human / 8% AI report remains an unassigned historical candidate until its stored representation is bound to the authorized Part-1 boundary. Never infer that score belongs to Part 1 merely because it was encountered during recovery.

## Bounded identity contract

Current long-document GUI identity no longer depends on the historical segmented-report DOM layout. It is bound through the read-only history record itself.

The matcher now accepts these representation modes, in order:

1. `exact_utf8` — literal equality;
2. `line_endings_normalized` — only CRLF/CR → LF differs;
3. `terminal_newlines_normalized` — only terminal newline count differs after line-ending normalization;
4. `outer_whitespace_normalized` — only outer boundary whitespace differs after line-ending normalization.

Every accepted mode must preserve the complete interior string and identical word count. The evidence receipt records:

- authorized source SHA-256 and word count;
- stored representation SHA-256 and word count;
- JSON field path where the representation matched;
- explicit `transport_match_mode`;
- record model/prediction metadata for provenance.

The raw history record remains in memory only.

### What is deliberately **not** accepted

Interior whitespace collapse is not an identity proof. For example, a stored single-space representation of source text containing paragraph breaks may be diagnostically related, but it cannot clear ambiguity merely because `" ".join(text.split())` matches.

If no bounded mode matches, the recovery path emits content-free comparison metadata for plausibly document-sized string fields:

- JSON field path;
- character/word counts and deltas;
- accepted match mode, if any;
- exact substring booleans;
- whitespace-collapsed equality as **diagnostic only**.

No stored text, record UUID, private URL, cookie, storage value, or credential is logged.

## Result-summary contract

The current rendered long-document overview exposes document-level Human/AI percentages but not historical per-segment word-count headings. Therefore:

- document identity comes from the bounded stored history representation;
- Human/AI fractions come from the bound report's rendered overview;
- the existence of `prediction` and `prediction_prob` fields does **not** establish the semantic orientation of `prediction_prob`; do not infer detector fractions from it;
- if rendered overview percentages cannot be parsed, fail closed;
- do not invent segment counts or segment text merely to satisfy the legacy parser.

This is a transport/layout correction, not a detector-science claim.

## Implementation

- `src/pangram_lab/history_api_record.py` — bounded stored-record identity plus content-free comparison diagnostics.
- `scripts/pangram_local_romance_recover_part1_api.py` — no-submit Part-1 recovery; no detector-action path.
- `scripts/pangram_local_romance_paid_api.py` — subsequent GUI paid runner; history-response listener is attached before detector activation.
- `scripts/pangram_local_romance_recover_resume_safe.sh` — operator entry point; Part 2 remains unreachable until Part 1 is recovered and cached.

For new GUI paid work, the paid reservation is durable before the click. After the click, failure to bind the exact/bounded stored record is ambiguous and blocks any repeat.

## Independent API transport

Joel's separate private self-hosted Pangram executor is now live and has produced a durable Pangram 4.0 `STAGE_SUCCESS` result. That API transport can be used for future measurements, but it does not retroactively clear this GUI Part-1 ambiguity. GUI development continues as an independent transport/recovery capability.

## Current stop boundary

- Do not resubmit Part 1 through GUI.
- Do not submit Part 2 through GUI until Part 1 is recovered and cached under an accepted bounded identity mode.
- If none of the accepted modes matches, preserve ambiguity and inspect the content-free representation diagnostic before changing the identity contract.
- If Part 2 is clicked but its stored record cannot be bound, preserve that call as ambiguous and recover before any repeat.
