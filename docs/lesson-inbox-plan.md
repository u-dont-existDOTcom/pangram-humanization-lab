# Lesson inbox implementation plan

Goal: automatically register each detector result for lesson review and process final dispositions through the existing trusted lesson-integrity Action using metadata-only requests.

1. Maintain an idempotent `state/LESSON-INBOX.json`: exact source path/ref/hash registers once, changed hash creates a new obligation, and stored entries contain detector triage metadata rather than source prose.
2. The fixed-batch runner registers a completed detector result before its final durable Git sync.
3. Metadata-only requests under `state/lesson-closeout-requests/` verify source ref/hash, record non-promoted or promoted dispositions through existing lesson-closeout logic, and leave an immutable processed receipt.
4. The existing `lesson-integrity.yml` workflow tests and processes requests with a scoped contents-write job. It receives no Pangram secret.
5. The weekly audit reads long-lived evidence refs and reports any inbox item that lacks a canonical main-branch ledger entry matching source path/ref/hash.
6. Verification requires focused request/queue tests plus the main full test and integrity gates.