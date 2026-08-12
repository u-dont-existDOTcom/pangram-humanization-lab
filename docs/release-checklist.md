# Release Checklist

The release ZIP is a reproducible snapshot of one Git commit.

Before delivery:

1. Run the full deterministic test suite.
2. Build with `python scripts/build_release.py --out <path>.zip --clean-zip-compile`.
3. Confirm the ZIP has one root directory and no `.git`, `.state`, `.venv`, caches, secrets, previous result ZIPs, or upload packages.
4. Confirm `INSTALL-AND-RUN.sh` and `RUN.sh` retain executable mode.
5. Confirm `MANIFEST.json` records source commit, graph version, policy version, exact member hashes, sizes, and executable flags.
6. Confirm `SHA256SUMS.txt` matches every source member listed in the manifest.
7. Confirm `PASTE_INTO_PROJECT_INSTRUCTIONS.txt` is under 8,000 characters.
8. Parse the project and policy authority manifests from the exact ZIP.
9. Confirm the installer performs a resolution-only pip report before first dependency installation, converts the full transitive result into a SHA-256 lock, and installs under `--require-hashes`; target resolution remains a live installation plane.
10. Treat clean-ZIP compilation as a deterministic plane. Dependency installation, LangGraph SQLite resume, Claude/Codex provider calls, Pangram calls, and research-provider checks remain separate live planes.
11. Do not claim a live plane passed from source hashes or mocked tests.

12. For autonomous self-healing releases, confirm repair Codex receives no Pangram/Brave credentials, protected project/policy/learning paths are hashed, source-hardcoding scans include repair tests, unsafe/testless repair plans are rejected before write-capable Codex, and promotion restarts with same-thread `resume` rather than `run`.
13. Confirm `scripts/reconcile_release_baseline.py` runs before the repairable installer pytest gate, `authorial_flow.bootstrap_repair` owns that exact preflight command, bounded bootstrap failure packages evidence automatically, and repair Codex sees the installed project venv first on `PATH`.
13. Do not transfer prior target-machine live status to a new repair commit: rerun the exact ZIP's real LangGraph promoted-repair checkpoint test and one end-to-end live repair before calling that plane verified.
14. For in-place upgrades over an existing installation, run the release-baseline reconciler after deterministic tests and before live smoke/runtime start. A dirty worktree may be committed only when every current release member matches `MANIFEST.json`/`SHA256SUMS.txt`, obsolete members come from the prior release manifest, and no unrelated changes exist. Preserve `.state`; never reset a clean existing head merely because the bundled release manifest is older than a promoted self-repair.
15. Exercise an old-release → new-release overlay with a checkpoint sentinel before delivery of a release that changes repair/baseline plumbing. Confirm the checkpoint bytes survive, Git becomes clean on the new local release baseline, and the new manifest records the expected source commit.
16. When upgrading a release that may preserve a terminal `bounded_machine_stop`, verify the new runtime replays the latest checkpoint whose `next` is the recorded failed node on the same thread, only once per program version; verify a bounded stop produced by the current program version is marked exhausted so a manual rerun does not replay providers again.
17. For the interactive-supervisor release, run the exact ZIP on the target Zorin machine with a deliberately bad-looking real Thought-Flow input. During a live Claude or Codex call, press Ctrl+C and confirm that partial child output is discarded or an atomic Pangram/repair update reaches a checkpoint first.
18. In the same terminal, ask one supervisor question and verify that the graph remains paused. Confirm one bounded redirect only after the controller displays its exact scope, invalidated fields, restart depth, and resume node.
19. Verify the confirmed action continues on the same thread without duplicating an accepted move, or type `leave paused` and prove the next `./RUN.sh` reopens the same durable session.
20. Record the first real Pangram task ID before polling, the returned detector version, and whether resume polled without another submission. A zero-task authentication probe is not evidence of candidate acceptance.
21. Do not approve the target Zorin plane until live Claude, Codex, Pangram, Ctrl+C, supervisor question, confirmed redirect, and same-thread continuation or durable continued pause all pass for the exact delivered ZIP.
22. For the 1.2 bounded-failure release, replay the captured semantic FAIL with an invalid natural-language escalation and prove it cannot reach generation.
23. Replay the arrival-with-uncovered-authority boundary. Confirm `STOP_BEFORE_CANDIDATE` stops or performs one validated rollback; unsafe rollback must produce `POLICY_CONTRADICTION` without another writer call.
24. Confirm every pressure/edge decision names the exact boundary ID and the rendered decision trace contains no source, accepted, candidate, prompt, transcript, or credential text.
25. Submit an approved-looking repair plan whose tests are prose. Confirm it is rejected before plan review, worktree creation, or write-capable Codex. Repeat its exact signature on unchanged evidence/program and confirm `NON_APPLICABLE_STOP` before a second review.
26. Exercise auth, unsupported-model, invalid-schema, structured-contract, and transient provider failures. Confirm typed attempt evidence and that no equivalent profile is retried.
27. Copy an existing 1.1 `.state` directory into a 1.2 checkout, run status/resume read-only checks, and compare checkpoint/evidence hashes before and after. Never delete or rewrite the original state during validation.
28. For Git delivery, verify the published branch tree equals the locally verified tree and record the exact commit. The upgrade command must create a backup ref for the prior head and preserve `.state`.
29. For 1.3 diagnostics publication, exercise installer pass, credential/account-action stops, bounded repair exhaustion, accepted completion, supervisor pause, repair restart, and unexpected interruption. Confirm each reaches the nonblocking publisher before any exit/`execv` boundary.
30. Publish through a real local bare remote and prove the source HEAD/status are unchanged, the diagnostics branch is append-only/idempotent, a push race never force-pushes, and a failed remote retains the outbox without changing the wrapped exit code.
31. Search every outbox record, remote commit, status file, and terminal status line for source/candidate/rejected prose, prompts, transcripts, stdout/stderr, exception text, credentials, environment values, full local paths, and evidence ZIP bytes.
