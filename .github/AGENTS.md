# GitHub automation instructions

Only `.github/workflows/pangram-paid-dispatch.yml` is executable on this evidence branch.

- Keep pull requests and ordinary pushes read-only and detector-free.
- Keep all remote Actions pinned to reviewed 40-character SHAs.
- Permit a paid job only for a push to the exact evidence ref that adds one immutable, hash-bound request/spec pair with no bundled change.
- Keep the automatic gate serialized, timeout-bounded, and dependent on the non-secret verify/preflight job.
- Scope `contents: write` and `PANGRAM_API_KEY` only to the detector job/step that commits exact evidence.
- Do not add task-specific paid workflows, commit-message paid triggers, or broad path-only paid triggers.
- Archive retired workflows outside `.github/workflows` with their original Git blob identities.
