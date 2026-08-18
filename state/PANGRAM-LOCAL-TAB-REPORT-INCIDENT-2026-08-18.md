# Pangram local Playwright tab/report incident — 2026-08-18

## Owner correction

Joel reported that the local Pangram automation was opening too many browser tabs and not closing them.

This is a real tooling defect, not cosmetic feedback. A persistent browser profile can restore tabs that were open at the previous shutdown. The first local implementation closed the Playwright context but did not explicitly normalize the tab set before shutdown, so old dashboard/report/login tabs accumulated across fresh runs.

## Paid Part 1 incident

Exact Romance Part 1:

- SHA-256: `ae88df0f4156537239cb984337196703b88629c3588a5e58ee50c0888d3b39f8`
- word count: 10,236
- audit: `romance-current-20496-pangram-gui-20260818`
- section: `romance-current-part-1`
- paid-call ledger: 1 reserved/submitted call, estimated 11 credits / USD 0.55

The call was durably reserved before the detector click and Pangram accepted the submission. The runner then failed at report capture with:

`Pangram report became visible but no analyzed segments could be parsed`

The saved `report-body.txt` contains the submitted article text/dashboard surface but no parseable report segments. Therefore the generic report-ready marker was insufficient: the runner remained bound to the dashboard while the actual result could be on another tab/page or otherwise not yet represented on that page.

The failure is correctly marked `detector_submission_attempted: true`; Part 1 is ambiguous and must not be resubmitted automatically. Part 2 was not submitted.

## Repairs

### Persistent tab hygiene

The local transport now:

- normalizes a normal automation launch to one working tab;
- explicitly closes every extra tab;
- before persistent-context shutdown, reduces the context to one tab and navigates that tab to `about:blank`;
- keeps the persistent profile for cookies/authentication, not as a growing browser-session/tab archive.

Ambiguous-result recovery may intentionally launch once without startup tab normalization so an already-paid result tab can be recovered. Cleanup still runs before that recovery session closes.

### Exact report binding

Paid-result completion no longer uses a generic `wait_for_report` marker as sufficient evidence. The local transport scans all current pages/tabs and accepts a report only when all of the following hold:

1. the report is bound to the exact submitted text by stable leading/trailing anchors;
2. Pangram report parsing yields analyzed segments (or a supported exact layout);
3. the parsed analyzed word count equals the exact submitted boundary.

The page satisfying those conditions becomes the evidence/report page for body/PDF capture. This handles same-tab and new-tab report behavior without guessing which tab Pangram used.

### Recovery before repeat

`scripts/pangram_local_romance_recover_part1.py` first inspects restored tabs for the already-paid Part 1 report. If necessary it attempts bounded, non-paid History navigation. It never clicks a detector action. Only a successfully exact-bound recovered report may clear the ambiguous failure and become the cached Part 1 result.

`scripts/pangram_local_romance_recover_resume_safe.sh` runs local tests, performs that no-repeat recovery, and resumes the paid runner only after recovery. If recovery fails, it stops with Part 1 still blocked and makes no repeat submission.

## Durable rule

For persistent-browser automation, session persistence is for authentication/state, not uncontrolled tab restoration. Normalize tabs explicitly. For asynchronous GUI work that may navigate or open a new tab, completion must be bound to the exact task/output artifact rather than inferred from a generic marker on the originally controlled page.

## Current stop boundary

Do not resubmit Part 1. Recover it from the existing Pangram result/History first. Do not submit Part 2 until Part 1 recovery succeeds and local tests pass.
