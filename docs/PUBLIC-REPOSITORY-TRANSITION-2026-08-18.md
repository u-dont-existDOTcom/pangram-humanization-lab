# Pangram public repository transition

Date opened: 2026-08-18
Completed: 2026-08-19
Status: **complete — public readback confirmed**
Repository: `u-dont-existDOTcom/pangram-humanization-lab`
Visibility: **public**

## Owner disclosure decision

The owner explicitly approved public disclosure of the Pangram test corpus and test evidence in this repository, including relationship/health/personal prose used as detector or authorship test material. Those tracked materials were not publication blockers.

This approval was specific to the repositories selected for publication. It did **not** authorize changing `u-dont-existDOTcom/AskRigor-lessons`; hosted readback after the transition confirms that repository remains private.

## Credential-disclosure audit

Before the visibility change, the publication audit scanned reachable Git history and hosted issue/PR/comment/review/release/Actions-log surfaces with pinned Gitleaks 8.29.1 and full value redaction.

The Pangram Git scan initially reported 86 `generic-api-key` heuristic matches. Exact historical-source review accounted for all 86 as non-secret Pangram metadata or synthetic test material:

- JSON `measurement_key` fields;
- JSON `first_human_measurement_key` fields;
- the exact synthetic security fixture `PANGRAM-SECRET-FIXTURE-4927` in its known regression/plan files.

A representative `first_human_measurement_key` value was `romance-r1-decomposition-r4-2026-08-13_STI_L57`, i.e. a detector measurement identifier, not a credential.

The final private hosted scan evidence reported zero hosted secret findings across 943 retrievable Actions logs; 57 older logs were unavailable/expired. `joel-articles` separately passed its publication-secret audit before the visibility mutation.

## Visibility mutation and readback

The installed GitHub CLI did not support the newer `gh repo edit --accept-visibility-change-consequences` flag. The owner therefore used the supported GitHub REST repository update through `gh api`, setting `visibility=public` for the three approved repositories.

Independent hosted readback on 2026-08-19 confirms:

- `u-dont-existDOTcom/pangram-humanization-lab` — **public**
- `u-dont-existDOTcom/joel-articles` — **public**
- `u-dont-existDOTcom/innerSignalArtifact` — **public**
- `u-dont-existDOTcom/AskRigor-lessons` — **private**

## Post-transition hosted controls

A fresh GitHub branch readback confirms Pangram `main` remains **unprotected** after the visibility transition. Public visibility removes the private GitHub-hosted Actions minute billing boundary for standard runners, but it does not itself establish branch rules or other security controls.

Secret scanning, push protection, Actions default permissions, vulnerability alerts, code-scanning posture, and evidence-branch protection must remain recorded as their actually verified states. Do not infer that public visibility enabled a control unless GitHub supplies a direct readback.

## Irreversibility

The public transition is an irreversible disclosure boundary in practice. Returning a repository to private later cannot retrieve public clones, forks, caches, or other copies.

## Follow-up

Repository-local metadata must describe the repository as public. Future cost work should treat public standard-runner Actions as free and should not reintroduce private-repository workarounds merely to save minutes. Paid provider calls and privileged/mutating workflows retain their existing explicit execution boundaries regardless of GitHub Actions minute cost.
