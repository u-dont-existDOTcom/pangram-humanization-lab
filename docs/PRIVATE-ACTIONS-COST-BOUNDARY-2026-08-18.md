# Private GitHub Actions cost boundary

Date: 2026-08-18
Status: implemented on `main`; Dharma-network follow-up in progress

## Goal

Reduce paid GitHub-hosted Actions minutes in this private repository without weakening the repository's privacy, detector-secret, evidence, or lesson-closeout boundaries.

This is an application of the canonical `u-dont-existDOTcom/universal-dev-architecture/patterns/paid-workflow-safety.md` private-repository cost boundary. It is not a competing CI framework.

## Privacy boundary

Cost reduction changes **where and when compute runs**, not what is public.

- Keep this repository private.
- Keep private/local prose, corpora, credentials, Pangram state, and any other existing local-only material within their current boundaries.
- Do not mirror private source into a public repository to obtain free Actions minutes.
- Do not use a public workflow plus a token to clone this private repository as a billing workaround.
- The Pangram paid-dispatch secret boundary and existing fail-closed registration topology remain unchanged.

## Execution classes

### Ordinary pull-request validation

`.github/workflows/lesson-integrity.yml` remains the complete deterministic PR gate. It runs the full test suite plus changed-range/current-ref lesson checks on GitHub's PR merge ref.

Superseded PR-head runs are cancellable. The same full gate no longer reruns automatically after merge to `main`.

`.github/workflows/repository-workflow-policy.yml` remains the repository-visible policy audit on pull requests and manual dispatch. It also no longer duplicates automatically on `main` push.

### Metadata mutation

`.github/workflows/lesson-closeout-requests.yml` is the isolated write-capable closeout processor. It runs only when `state/lesson-closeout-requests/**` changes on an eligible same-repository pull request. It is non-cancellable because it may commit durable metadata.

This preserves privilege isolation without paying for a second setup/install/test job on every unrelated PR.

### Heavy research execution

A workflow containing this marker is an explicit manual research execution boundary:

```text
# actions-cost-class: manual-heavy-research
```

Marked workflows must expose `workflow_dispatch` and must not expose `pull_request`, `push`, or `schedule` triggers. `tests/test_private_actions_cost_policy.py` enforces that invariant.

The current migrated set includes:

- `idiolect-luar-matched-pilot.yml`
- `idiolect-content-light-matched-control.yml`
- `idiolect-luar-content-controls.yml`
- `idiolect-snapshot-repro-audit.yml`
- `idiolect-transformation-sensitivity.yml`
- `idiolect-dharma-author-census.yml`
- `idiolect-dharma-profile-census.yml`
- `idiolect-dharma-control-profile-extract.yml`
- `idiolect-ordinary-control-census.yml`

Their research steps, pinned models, acquisition behavior, privacy checks, and metadata-only artifacts remain unchanged. Only automatic hosted execution is removed.

The Dharma network workflows share a non-cancellable source-network concurrency group. This does not make parallel jobs wait across already-started runs when GitHub has already scheduled them, but it prevents a manually requested source-network operation from being silently superseded or cancelled halfway through a rate-limited evidence acquisition.

## Shared-path fan-out incident

During the hard-negative control-author work, an initial implementation extended the shared `src/pangram_lab/dharma_author_discover.py` module. Three pre-existing workflows listed that path in automatic pull-request filters:

- Dharma author census;
- Dharma profile census;
- Dharma control-profile extraction.

All three were activated even though the intended task required only deterministic code changes and a new, separately controlled census. The runs succeeded, but consumed private Actions minutes and repeated public-source work unnecessarily.

The shared-file change was reverted and the new one-pass census was isolated in its own module. The durable rule is broader:

> Before editing a shared path in a cost-sensitive repository, inspect every workflow whose path filter includes that path. Treat the resulting trigger fan-out as part of the change's execution cost and external-side-effect surface.

When the desired extension does not need to alter the old behavior, prefer a separate module whose only live workflow is manual-only. When a shared edit is genuinely necessary, first convert or explicitly justify every automatically triggered live-network/model workflow. Do not discover the trigger graph by paying for it.

## New heavy workflows

A new expensive research workflow should normally be registered on `main` as manual-only before it is needed on another branch, because GitHub manual dispatch registration is default-branch dependent. If pre-merge branch execution is genuinely required, use the established fail-closed registration pattern rather than reintroducing automatic PR execution.

Deterministic code/fixture/invariant tests belong in the ordinary PR suite. Live acquisition, model benchmarking, rate-limit sleeps, paid-provider work, and comparable experiment execution belong behind the manual boundary unless a project-specific requirement explicitly justifies automatic hosted spend.

## Post-merge validation tradeoff

This repository has no verified default-branch protection/ruleset enforcing a second merge-head suite. The PR gate checks the GitHub-generated merge ref before merge. The weekly lesson audit remains a durable backstop for `main` and the long-lived evidence branch.

If a future risk model requires exact post-merge execution, add only the materially distinct minimal check needed and record why the extra billed job is necessary; do not restore duplicate full-suite and policy jobs by default.

## Self-hosted threshold

Do not put an Actions runner on the AskRigor production server or another machine holding unrelated consequential secrets merely to avoid hosted-minute charges. If private hosted usage remains materially above the included allowance after trigger reduction, evaluate a repository-scoped isolated runner on a trusted spare machine or dedicated CI VM.

A self-hosted runner is a separate trust boundary and should not be shared with public repositories. Trigger reduction comes first; caching and self-hosting are second-order optimizations.

## Regression contract

`tests/test_private_actions_cost_policy.py` fails if:

- a marked heavy research workflow regains an automatic trigger;
- a known live Dharma source-network workflow lacks the manual-heavy marker or shared concurrency boundary;
- ordinary validation regains automatic `main`-push duplication;
- superseded read-only PR validation stops being cancellable; or
- closeout mutation loses its narrow request-path trigger/non-cancellable boundary.
