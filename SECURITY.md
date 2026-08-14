# Security policy

This is a private, high-risk repository because its automation can access a paid detector credential.

Do not disclose a suspected credential, task identifier, private detector evidence, or exploit in an issue, pull-request comment, workflow log, artifact, or commit. Report it to the repository owner through an existing private channel or the repository's private Security interface when available.

If a credential may have been exposed, stop paid workflows, preserve non-secret evidence, rotate the credential at its provider, and review Git history and Actions logs before resuming. Never print the Pangram key to diagnose access.

Security-sensitive paths are routed through `.github/CODEOWNERS`. A normal pull request must use read-only permissions unless a narrowly scoped job documents why a write permission is required.
