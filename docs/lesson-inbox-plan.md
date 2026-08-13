# Lesson inbox implementation plan

Goal: automatically register each detector result for lesson review and process final dispositions through a pre-installed metadata-only GitHub Action.

1. Write tests for an idempotent `state/LESSON-INBOX.json`: exact source hash registers once, changed hash creates a new obligation, resolving requires exact path/ref/hash, and stored entries contain metadata rather than source prose. Verify the tests fail before implementation; then implement `src/pangram_lab/lesson_inbox.py` and make them pass.
2. Write a failing runner test proving a completed fixed-batch result registers its result path/hash plus experiment/audit/section metadata. Wire registration into `scripts/run_fixed_batch.py` before final Git sync; make the test pass.
3. Write tests for a metadata-only closeout request processor: verify source ref/hash, record non-promoted and promoted dispositions through existing lesson-closeout logic, resolve only the matching inbox item, preserve an immutable processing receipt, and reject changed source hashes. Implement `src/pangram_lab/lesson_request.py` plus `scripts/process_lesson_closeout_request.py`.
4. Install one main-branch workflow triggered only by closeout-request and processor paths. It runs tests, processes requests with `contents: write`, audits lesson integrity, commits, and pushes. It receives no Pangram secret.
5. Extend the weekly lesson audit so pending inbox items are reported until resolved.
6. Run focused tests and full `pytest -q` in GitHub Actions, then a synthetic metadata-only smoke closeout. Verify inbox/request files contain no article body or detector credentials before merging.