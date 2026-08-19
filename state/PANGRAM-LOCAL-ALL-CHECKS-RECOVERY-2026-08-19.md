# Pangram local All Checks recovery checkpoint — 2026-08-19

## Live owner-machine result

The latest no-repeat recovery run on Joel's Zorin machine completed the full deterministic gate at **179/179 passed**.

Safety state remained intact:

- exact Romance Part 1 was **not** submitted again;
- exact Romance Part 2 was **not** submitted;
- Part 1 remains blocked as an ambiguous already-paid action;
- the dedicated automation profile remained the only browser profile used.

The recovery still did not locate the Part 1 result. Chromium history again produced zero `/history/<UUID>` candidates, and the authenticated dashboard ended on `/dashboard` with no report markers.

## New current-UI evidence

Fresh official Pangram product material shows that past detector records are currently surfaced under an **All Checks** page/table, with rows exposing **View Results** actions. Pangram's privacy material still states that registered dashboard submissions remain available in account history while the account is active.

The previous recovery implementation was biased toward older labels/routes containing `History`, `scans`, or `reports`. That can miss the current UI even when the record is present.

## Repair after the 179/179 run

The branch now broadens read-only recovery to current Pangram terminology:

- navigation vocabulary includes `All Checks`, `checks`, past/recent checks, records, plus the prior History/scans/reports labels;
- rendered navigation selection uses **control label text as well as route text**, so an `All Checks` link can be followed even if its href does not contain `history`;
- explicit `View Results` same-origin links are tried read-only even when the current route is not `/history/<UUID>`;
- in-memory JSON result identity ancestry includes `check`, `document`, `submission`, and `analysis` in addition to the older history/result/scan/detection/request vocabulary;
- JSON candidate extraction may inspect JSON responses from a backend host other than `pangram.com`, but only result identities survive and every candidate still must exact-bind to the Part-1 text plus the 10,236-word boundary;
- a collapsed menu/sidebar may be opened once only through an explicitly labelled navigation/menu control before retrying All Checks/History controls.

## Privacy-bounded structural diagnostic

If the exact report still cannot be recovered, the recovery writes:

`~/Téléchargements/pangram-local-history-structure-diagnostic.json`

It contains only structural evidence needed to repair the selector/network path:

- redacted safe current-page metadata;
- visible interactive labels, with emails/long opaque tokens redacted;
- counts of Chromium-history and network-derived result candidates;
- response host + redacted path + status + content type + method;
- JSON response **key shapes only**, not values.

It deliberately excludes submitted text, response bodies, query strings, cookies, storage values, header values, credentials, and private result URLs.

## Stop boundary

Do not resubmit Part 1. Do not submit Part 2 before exact Part-1 recovery succeeds. The next owner-machine run is a validation/recovery run for the new All Checks path; if it still fails, use the structural diagnostic rather than guessing another UI selector.
