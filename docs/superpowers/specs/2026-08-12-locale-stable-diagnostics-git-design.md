# Locale-Stable Diagnostics Git Transport Design

**Status:** Authorized corrective work for the approved automatic diagnostics design.

**Baseline:** `1.3.0-dev1` at local commit `cc910f53525d2af7a24175bc28c4282d17732c14`.

**Preservation mode:** P0 for article, project, policy, owner-gold, semantic-gold, and promoted learning material. This change is operational only.

## Reproduced defect

Joel's first manual publication attempt selected the canonical diagnostics remote but returned `GIT_FAILURE` after one attempt while the remote diagnostics branch did not yet exist. The transport distinguishes that normal first-publication condition by matching the English Git sentence `couldn't find remote ref`. It also classifies authentication and network failures from English Git stderr tokens. On a French Zorin locale, translated Git messages bypass those checks and collapse into `GIT_FAILURE`.

A proposed shell probe using `LC_ALL=C` exposed a second boundary hazard before Authorial Flow started: Python selected an ASCII filesystem encoding and failed while importing from a virtual environment beneath `~/Téléchargements`. The probe was also launched from a different project directory, so the Authorial Flow outbox was not changed.

## Approaches considered

1. **Stabilize only Git's message locale (chosen).** Set `LC_MESSAGES=C` and `LANGUAGE=C` in the environment passed to diagnostics Git child processes. Remove a child-level `LC_ALL`, which would otherwise override `LC_MESSAGES`, while explicitly preserving its effective character-type value as `LC_CTYPE`. Preserve `LANG`, the parent process, and credential-helper configuration. This removes localization from the existing classifier without making Python or non-ASCII paths use ASCII.
2. **Probe every branch with `git ls-remote --exit-code`.** This avoids parsing the missing-ref message, but adds a network round trip to every successful publication and still leaves authentication/network classification locale-sensitive.
3. **Recognize translated messages.** This is incomplete by construction and would require maintaining a growing language-specific token table.

## Selected behavior

`_git_result` owns the Git subprocess boundary. It will copy the caller environment, derive the effective character-type locale from `LC_CTYPE`, then `LC_ALL`, then `LANG`, remove `LC_ALL` from the child, restore that value as `LC_CTYPE`, and set `LC_MESSAGES=C` plus `LANGUAGE=C`. This forces only message translation to the stable C language while retaining the caller's character encoding and all other inherited environment needed by Git credential helpers. Prompt suppression remains unchanged.

The queue, record allowlist, branch name, canonical repository check, retry policy, disposable checkout, source checkout isolation, and terminal status format do not change. Existing queued records remain byte-for-byte untouched and publish normally on the next successful attempt.

## Error handling and privacy

The fix does not persist or print raw Git stderr. Once Git emits stable English diagnostic text, the existing typed classes (`AUTH_REQUIRED`, `NETWORK_UNAVAILABLE`, `NON_FAST_FORWARD`, and the first-publication orphan path) become deterministic. Unknown failures still fall back to `GIT_FAILURE` without exposing message bodies.

## Tests

1. A regression launches a real fake `git` executable from a non-ASCII `Téléchargements`-style path while the inherited message locale is French. The fake emits a localized missing-ref message unless its child environment receives `LC_MESSAGES=C` and `LANGUAGE=C`. The expected result is the existing `orphan` branch-creation path.
2. The test starts with a French UTF-8 `LC_ALL`, then asserts that the Git child receives no overriding `LC_ALL` and retains `LC_CTYPE=fr_FR.UTF-8`, proving the fix does not recreate the Python ASCII-path crash.
3. Existing local bare-remote integration tests continue proving orphan-branch creation, append-only publication, queue flushing, idempotency, race retry, and source-worktree isolation.
4. The complete deterministic suite and clean release build must pass before publication.

## Live acceptance

From the installed Authorial Flow directory, the content-free probe is:

```bash
LC_MESSAGES=C LANGUAGE=C ./RUN.sh publish-results
```

Success is `diagnostics_status=published` or `diagnostics_status=already_published`, followed by the appearance of `diagnostics/authorial-flow-graph-v1` in the canonical private repository and remote inspection of the two queued allowlisted records.
