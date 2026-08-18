# Pangram public repository transition

Date: 2026-08-18
Status: pre-publication audit pending
Target repository: `u-dont-existDOTcom/pangram-humanization-lab`
Target visibility: public

## Owner disclosure decision

The owner explicitly approved public disclosure of the Pangram test corpus and test evidence currently in this repository, including relationship/health/personal prose used as detector or authorship test material. These tracked materials are not treated as publication blockers for this transition.

This approval is specific to Pangram's repository/test evidence. It does **not** authorize changing `u-dont-existDOTcom/AskRigor-lessons` from private; that repository remains excluded from this transition.

## Remaining blocker

The remaining pre-disclosure blocker is credential/private-key exposure, not personal-test-content exposure. Before changing visibility, the repository must pass `.github/workflows/publication-secret-audit.yml` on the exact preparation head and again from `main` immediately before the hosted visibility toggle.

The audit reuses the established Inner Signal publication-audit baseline rather than inventing a new secret detector:

- Gitleaks `8.29.1`;
- Linux x64 archive SHA-256 `e4eb209d04e20339d77122a3bdf9cd41351255cfb27ebcb75e85325e04f88924`;
- full redaction of detected secret values;
- all currently reachable branches, tags, and pull-request heads;
- commit messages and ref names;
- issue and pull-request bodies;
- issue comments and inline review comments;
- pull-request review bodies;
- release metadata;
- retained GitHub Actions logs that the authenticated repository owner can still retrieve.

The audit reports only counts/status, never matching secret values. Temporary scanner output is mode-restricted and deleted at process exit.

## Explicit limits

The scan is a disclosure-risk control, not a mathematical proof that no secret can exist. Expired/unavailable Actions logs cannot be disclosed through GitHub and are counted separately. Historical workflow artifacts are not downloaded by this audit; existing Pangram research workflows intentionally store metadata-only result artifacts, and the owner has approved disclosure of the test material itself. GitHub-hosted controls must be re-read after the visibility transition because plan-dependent settings can change when a repository becomes public.

Changing a repository back to private later cannot retrieve public clones, forks, caches, or other copies. The visibility change is therefore treated as an irreversible disclosure boundary.

## Execution order

1. Keep repository visibility private.
2. Merge this preparation only after deterministic CI and the publication secret audit are reviewed.
3. From private `main`, manually run **Publication secret audit** one final time.
4. Change repository visibility to public in GitHub settings.
5. Read back `visibility=public` from GitHub.
6. Update repository profile/README/current state from transitional-private to actual public state.
7. Recheck branch protections, secret scanning/push protection, code scanning, Actions policy, and any other plan-dependent hosted controls.
8. Record final public-transition evidence in Git.

## Tool boundary

The connected ChatGPT GitHub integration can prepare code, workflows, commits, pull requests, merges, and readback, but currently exposes no repository-visibility mutation action. The hosted visibility toggle therefore remains the single required owner UI action after all preconditions are green.
