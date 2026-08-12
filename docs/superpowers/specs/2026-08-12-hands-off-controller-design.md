# Hands-Off Update, Repair, and Resume Controller Design

**Status:** Approved by Joel on 2026-08-12. Joel selected automatic execution of verified updates and then authorized implementation with “build it.”

**Preservation mode:** P0 for project inputs, article text, policy, owner labels, learning records, detector baselines, and existing LangGraph state. This feature changes installation, update, recovery, and diagnostics control only.

## Goal

Replace the repeated human courier loop—run on Zorin, publish diagnostics, ask Work to inspect them, receive a patch, pull, and run again—with one persistent, idempotent controller. After one final bootstrap, Joel runs `./INSTALL-AND-RUN.sh`; the controller updates, verifies, installs, starts or resumes the exact thread, repairs machine failures, publishes evidence, accepts verified remote repairs, and continues without routine clicks.

Joel remains responsible only for irreducible human boundaries: credentials or account access, an unsafe Git trust divergence, and substantive authorial or policy decisions. He is never asked to identify, collect, package, or relay routine logs.

## Approaches considered

### 1. Local persistent controller plus GitHub rescue watch — selected

The local process is the primary owner because it has the exact checkout, `.state`, provider CLIs, authenticated Git remote, and private evidence. A separate hourly ChatGPT Work condition watch reads the privacy-safe GitHub diagnostics and repair capsule branches. It acts only when a new machine failure remains unresolved and only publishes a repair after executing the repository’s declared regression and full verification gates.

This design gives immediate local recovery and a separate observer for failures in the recovery layer itself, without requiring Joel to buy or manage an API key for GitHub Actions.

### 2. Local controller only

This is immediate and keeps all evidence local, but no independent process notices if the outer controller exhausts or crashes. It removes most clicking but not the final “check results” escalation.

### 3. GitHub Actions repair worker

This can react immediately to a diagnostics push, but it needs hosted secrets, billable model/API access, and a second execution environment. It adds more credential and supply-chain surface than the current private-repository and locally authenticated CLI design requires.

## User-visible contract

`INSTALL-AND-RUN.sh` remains the only normal entry point. It stays in the foreground so the existing live work feed and same-terminal Ctrl+C supervisor remain available.

The controller prints concise phase changes:

- checking trusted update channel;
- candidate update verification;
- installation or dependency reconciliation;
- starting or resuming the exact thread;
- local repair, verification, promotion, or restart;
- waiting for a remote repair after bounded local exhaustion;
- a typed human stop with the one action that cannot be automated.

It does not print raw prompts, provider transcripts, credentials, article content from diagnostics, or hidden reasoning.

## Architecture

### Stable bootstrap and update channel

A small standard-library bootstrap layer runs before the project virtual environment. The permanent trusted remote channel is the private branch `install/authorial-flow-graph-v1`. The one-time rollout may fast-forward the existing versioned local branch from that channel; future releases advance the stable channel, so Joel never needs a new branch-specific command.

`INSTALL-AND-RUN.sh` is only the entry wrapper. Before fetching or changing the checkout, it copies the currently trusted bootstrap implementation into a commit-addressed directory under `.state/controller/bootstrap/` and `exec`s that immutable snapshot. The running updater therefore never reads a script that it is concurrently replacing. Candidate bootstrap code is not launched from the working tree; it becomes eligible for the next process only after the detached candidate worktree passes all gates and promotion completes.

The bootstrap:

1. acquires one controller lock under `.state/controller/`;
2. retries queued diagnostics publication without changing the run result;
3. fetches only the configured remote and stable install branch;
4. rejects deletion, non-fast-forward history, an untrusted remote URL, or a dirty checkout outside a controller-recorded verified repair overlay;
5. records the current commit as last-known-good;
6. stages a newer candidate in a detached temporary Git worktree;
7. verifies release metadata, protected-input hashes, dependency resolution, targeted update tests, and the full deterministic suite there;
8. runs state migration against a disposable copy of `.state`;
9. fast-forwards the installed checkout only after every candidate gate passes;
10. reconciles dependencies and performs live capability smoke only when the accepted program or dependency lock changed.

Candidate failure leaves the installed checkout and live `.state` untouched. The controller publishes a typed `update_rejected` result and keeps running the last-known-good program.

### Typed child outcome protocol

The controller never infers control flow by scraping terminal prose. Every `run` or `resume` invocation atomically replaces `.state/controller/last-outcome.json` with a versioned, content-free record containing the outcome kind, program commit, thread ID, failure signature, origin node, and permitted evidence references.

The child exit code and record must agree:

| Exit | Outcome | Controller action |
|---:|---|---|
| 0 | `accepted` or `completed` | publish result and exit successfully |
| 20 | `owner_pause` | keep the same checkpoint and supervisor session; exit normally |
| 21 | `owner_decision_required` | display the exact authorial decision and stop |
| 22 | `credential_required` | request only the named credential through the existing private terminal path |
| 23 | `account_action_required` | display the exact account action and stop |
| 75 | `machine_restart` | reload the installed program and resume the same thread immediately |
| 76 | `bounded_machine_stop` | invoke outer repair; never ask Joel to relay logs |
| 130 | `owner_interrupt` | enter or preserve the existing same-terminal supervisor boundary |

A missing, stale, malformed, or contradictory outcome record is itself a typed controller failure and enters the outer repair path.

### Persistent run supervisor

After installation, the shell retains ownership instead of `exec`-replacing itself with `RUN.sh`. It launches the runtime as a child, renders its existing work feed, reads the typed outcome, and selects the next deterministic action.

The supervisor preserves:

- `.state` and the exact content-addressed thread;
- pending Pangram task ownership;
- current supervisor interrupts and conversations;
- accepted moves and immutable authority inputs;
- repair budgets keyed by program commit plus failure signature;
- the last-known-good update and migration backup.

Concurrent controller starts fail closed with the owning PID and start time. A stale lock is reclaimed only after deterministic process and boot-identity checks.

### Outer repair controller

The existing in-graph and installer repair paths remain first-line recovery. The new outer repair layer catches failures that occur outside those paths, including CLI dispatch, terminal recovery selection, outcome serialization, installer control, and controller/runtime handoff.

For one program commit plus failure signature it permits one initial Codex repair and one correction. It reuses the existing secret-redacted evidence builder, isolated Git worktree, protected-path enforcement, regression-first contract, independent plan/diff review, targeted gates, and full-suite verification.

A verified repair is promoted locally, tagged with its failure/run identity, and pushed as a fast-forward commit to the stable install branch only if the remote branch still equals the repair base. If the remote advanced concurrently, the controller discards the stale promotion candidate, verifies the newer remote program, and retries the original thread there; it never force-pushes, guesses at a merge, or overwrites another repair.

After promotion the old child exits with `machine_restart`; the persistent supervisor reloads the new image and resumes the same checkpoint. Repeating the same failure on the repaired program consumes the bounded budget and proceeds to remote rescue instead of looping models indefinitely.

### Privacy-safe remote repair capsule

The compact diagnostics branch remains content-free. A second orphan branch, `repairs/authorial-flow-graph-v1`, carries only the additional machine evidence required for an independent code repair:

- run ID, failure signature, program and install commits;
- failure class, phase, origin node, typed exit, and retry counts;
- repository-relative stack frames and exception class, when allowlisted;
- exact declared regression command and bounded test output only after secret, absolute-path, prompt, transcript, and article-content exclusion checks;
- hashes and local-only references for larger evidence that is not uploaded;
- repair-attempt dispositions and the commit that superseded the failure.

If the allowlist cannot prove a field safe, that field is omitted. Article text, project-source prose, prompts, transcripts, raw provider output, environments, credentials, home paths, and evidence ZIP bytes are never published.

### GitHub rescue watch

An hourly condition watch is the slow outermost breaker, not the normal scheduler. It checks the diagnostics and repair branches for a new unresolved `bounded_machine_stop`. A failure is resolved when a later result for the same thread and failure lineage is accepted, completed, restarted on a newer program, or explicitly linked to a verified repair commit.

The watch may change the stable install branch only when it can:

1. reconstruct the defect from the safe capsule and repository;
2. add or identify a regression that fails before the patch;
3. run the regression, integration gates, protected-path checks, and full suite;
4. create a commit whose parent is still the stable branch head;
5. fast-forward the branch without force.

If its environment cannot run those gates or the capsule is insufficient, it leaves code unchanged and records a typed `remote_repair_blocked` disposition. It alerts Joel only when the blocker is an irreducible credential, account, repository-permission, or authorial decision; it does not ask him to collect logs.

## Update and rollback safety

The controller stages before promotion, so most rejected updates need no rollback. Before a promoted program touches live state, the controller creates an atomic migration backup containing the SQLite checkpoint store and controller metadata. Migration failure restores that backup and keeps the old program.

After a new program has committed valid runtime progress, recovery is repair-forward. The controller does not silently roll back program and state across a potentially irreversible checkpoint migration. A rollback after that boundary requires an explicitly declared reversible migration and an exact matching backup.

The stable channel never accepts force-pushed history. Remote URL, branch, candidate commit, release metadata hash, and last-known-good commit are written to the controller journal for every update decision.

## Stop and wait behavior

The controller may stop for:

- a named credential that cannot be obtained non-interactively;
- a named account/payment/login action;
- an owner pause or substantive authorial/policy decision;
- untrusted remote identity, non-fast-forward history, protected-input drift, or concurrent Git ownership;
- a repair capsule that cannot safely contain enough evidence and a remote repair that cannot be verified.

Network outages, transient Git failures, provider timeouts, stale diagnostics queues, and the absence of a newer remote repair do not stop the controller. They enter bounded exponential backoff with visible next-attempt time. Backoff resets when the remote head, program commit, failure signature, credential state, or network state materially changes.

## State and ownership

New local state lives under `.state/controller/`:

- `lock.json` — PID, boot identity, process start, and controller version;
- `config.json` — trusted remote identity and stable install branch;
- `last-outcome.json` — atomic typed child outcome;
- `journal.jsonl` — content-free controller transitions;
- `repair-ledger.json` — bounded attempt identity and disposition;
- `last-known-good.json` — verified commit and migration boundary;
- `bootstrap/` — commit-addressed immutable copies of the trusted running controller;
- `migration-backups/` — bounded local-only state snapshots;
- `update-worktrees.json` — cleanup and ownership records.

The deterministic controller owns Git fetching, ancestry checks, locks, hashes, state copies, migrations, test execution, promotion, push leases, retries, and rollback. Models may diagnose and propose code changes only inside isolated repair worktrees. They cannot approve their own patch, alter protected article/policy authority, see controller-only credentials, or bypass a failed gate.

## Test-first acceptance criteria

### Update controller

1. No remote change starts or resumes without rerunning unnecessary install gates.
2. A fast-forward candidate is staged, fully verified, promoted, and recorded without touching `.state` content.
3. A non-fast-forward, wrong remote, dirty unrelated file, bad manifest, protected drift, failed dependency resolution, failed test, or failed migration is rejected without changing installed HEAD or live `.state`.
4. An accepted dependency/program change runs the required install and live-smoke gates exactly once.
5. A simulated Git/network outage queues diagnostics and retries without losing the thread.

### Outcome and loop control

6. Every typed outcome selects the documented next action without parsing stdout.
7. Missing, stale, malformed, and exit-mismatched outcome records enter bounded outer repair.
8. `machine_restart` reloads code and resumes the same thread/checkpoint.
9. Credential, account, owner-decision, and owner-pause outcomes never invoke code repair.
10. Two concurrent controllers cannot mutate one checkout or thread; stale-lock recovery is deterministic.

### Repair and Git coordination

11. A CLI-dispatch or terminal-recovery regression outside the graph reaches outer repair automatically.
12. Repair demonstrates RED before patch and GREEN afterward, passes all existing gates, preserves protected hashes, promotes once, and resumes.
13. The same unchanged failure cannot consume an unbounded number of model calls.
14. A concurrent remote advance prevents the stale repair push; the newer remote candidate is verified and tried first.
15. No repair uses force-push or silently merges competing histories.

### Privacy and rescue watch

16. Secret fixtures, absolute home paths, prompts, transcripts, article sentences, raw environments, and evidence ZIP bytes are absent from both remote branches.
17. Unsafe test output is omitted rather than weakly redacted.
18. The watch ignores resolved and already-attempted failures.
19. The watch cannot publish unless RED/GREEN, integration, full-suite, protected-path, and current-parent gates all execute successfully.
20. An unverifiable remote repair records a blocked disposition and leaves the install branch unchanged.

### Target-machine acceptance

21. On Joel’s French Zorin checkout under `~/Téléchargements`, one bootstrap command installs the controller and starts the existing thread.
22. A deliberately broken runtime path publishes diagnostics, repairs locally or through the rescue path, receives the verified fast-forward update, and resumes without another terminal command or “check results” message.
23. Ctrl+C still opens the same-terminal supervisor, and leaving it paused survives controller restart.
24. A real credentials stop names only the required action and resumes after the credential is supplied.

## Non-goals

- Unbounded autonomous code repair.
- Automatic authorial, therapy, policy, or detector-baseline decisions.
- Force-pushing, autonomous conflict resolution, or trusting arbitrary forks/remotes.
- Uploading private evidence packages or user prose to GitHub.
- A background daemon that hides the existing live work feed.
- Replacing the LangGraph checkpoint store or existing supervisor UI.
- Treating a scheduled Work task as evidence that tests passed when it could not execute them.

## Rollout boundary

The rollout creates the stable private install branch, lands the controller and tests there, and updates the current versioned install branch to the same verified commit for compatibility. Joel performs one final fast-forward bootstrap from `~/Téléchargements/authorial-flow-graph-v1`. From that point onward, `INSTALL-AND-RUN.sh` owns update, install, run, repair, diagnostics, and same-thread continuation.

The feature is complete only after the deterministic suite passes from a clean extraction and the exact target-machine failure-to-repair-to-resume acceptance run succeeds without manual log transfer or a second command.
