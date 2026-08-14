# GitHub automation instructions

Only `.github/workflows/pangram-fixed-batch.yml` is executable on this evidence branch.

- Keep push and pull-request jobs read-only and detector-free.
- Keep all remote Actions pinned to reviewed 40-character SHAs.
- Keep the paid job manual-only, serialized, timeout-bounded, and dependent on the non-secret preflight job.
- Scope `contents: write` and `PANGRAM_API_KEY` only to the detector job/step that commits exact evidence.
- Do not add task-specific push triggers or commit-message paid triggers.
- Archive retired workflows outside `.github/workflows` with their original Git blob identities.
