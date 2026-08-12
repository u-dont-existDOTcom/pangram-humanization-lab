# Dependency Verification

Build-time dependency check: 2026-08-11.

- `dspy==3.2.1` remains the latest stable DSPy release on PyPI; `3.3.0b1` is a pre-release.
- DSPy's official documentation shows GEPA construction with `dspy.GEPA(metric=..., auto="medium")` and program optimization through `.compile(...)`.
- DSPy is an optional optimizer dependency only. The article-writing hot path does not import it.
- The project deliberately keeps the Claude/Codex bridge independent of DSPy's LM inheritance API. That avoids coupling the core CLI/secret/heartbeat behavior to a more volatile optional interface.

Primary references checked:

- https://pypi.org/project/dspy/3.2.1/
- https://dspy.ai/

The disposable build environment cannot install optional network dependencies. The release installer therefore repeats dependency installation and the optional-extra smoke test on the target machine when the optimizer extra is requested.

## Runtime dependency lock protocol

The release carries exact direct requirement inputs in `requirements.lock`. On the first target-machine installation for a given source hash, the installer uses `pip install --dry-run --ignore-installed --report` to resolve the complete transitive environment **without installing project dependencies**. `scripts/resolve_dependency_lock.py` then converts every resolved artifact into `.state/dependencies/requirements.resolved.lock` with its exact version and SHA-256. The actual environment install uses `pip install --require-hashes` against that persisted full lock. The lock metadata records the source-input hash, pip-report hash, resolved-lock hash, and package count; reruns reuse it only while both the source-input hash and lock hash still match.

The build container cannot perform the networked resolution itself. The exact target-machine artifact set therefore remains a live installation-plane result and is automatically preserved in the evidence package.
