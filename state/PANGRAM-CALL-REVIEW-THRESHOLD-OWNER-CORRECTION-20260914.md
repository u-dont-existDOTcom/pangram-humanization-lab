# Pangram paid-call review threshold — owner correction

Date: 2026-09-14
Status: **CURRENT OWNER CORRECTION / DETECTOR-OPERATIONS POLICY**

Joel clarified that the standing six-new-paid-calls figure for a stable audit/section is a **review threshold, not an absolute universal maximum**.

Owner meaning: after six paid calls, do not continue reflexively. Going past six requires a good, concrete reason. The reason should identify what unresolved decision the additional calls can change and why the existing evidence is insufficient.

Operational rule:

1. Keep one stable audit/section identity. Do not create a nominally new audit merely to reset accounting.
2. Before any paid call, still check exact cache, completed result, pending task/report, and ambiguous transport state. Never rebuy a completed or potentially already-paid exact measurement.
3. Up to six new paid calls remains the default bounded budget for a stable audit/section.
4. More than six requires explicit owner authorization plus a concrete decision-relevant rationale.
5. Record the authorized higher execution ceiling and rationale durably with the same audit ledger before/with the next paid reservation.
6. A prior extension is not blanket authorization for endless detector iteration. Reassess at the newly authorized ceiling or when the experiment's causal premise changes.
7. Prefer a materially different discriminating test over more same-method local tweaking when earlier predictions fail.

The `automation/pangram-fixed-batch` implementation was updated on 2026-09-14 to support this policy: six is the default review threshold; a higher `section_call_cap` must be accompanied by a non-empty `owner_override_reason`; the existing ledger is extended monotonically and records the override.

Live validation occurred in audit `somatic-hidden-human-signal-ab-20260914`: the first six calls all returned Human, Joel authorized four specific R1/R2 calls, the same ledger was extended from 6 to 10 with the rationale recorded, and the four additional calls completed without resetting prior accounting.

This policy governs paid-call budgeting only. It does not make Pangram an authority over article quality, fidelity, authorship, or publication.