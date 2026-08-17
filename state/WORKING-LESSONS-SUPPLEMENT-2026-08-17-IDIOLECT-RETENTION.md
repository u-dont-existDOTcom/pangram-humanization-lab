# Working humanization lessons supplement — idiolect retention, 2026-08-17

Read after the earlier working lessons and supplements. This file adds a research-backed authorship-signal preservation layer; it does not weaken owner authority, semantic fidelity, architecture, or the existing Pangram completion gate.
<!-- closeout-request:idiolect-retention-research-integration-2026-08-17 -->
## Authorship-signal retention is a separate gate

Malik and Awan's IER study shows that extensive generative rewriting can preserve semantic content while substantially reducing recoverable authorship signals. Grammar-only correction caused much less erasure, and a prompt explicitly asking the assistant to preserve the author's voice still left most deep authorship signal unrecovered.

Durable rules:

- **A voice-preservation prompt is an instruction, not validation.**
- Use the minimum edit dose that solves the actual defect. Prefer mechanical correction and local repair over full regeneration; prefer actual owner wording and thought routes over assistant reconstruction.
- Keep three results separate: semantic/editorial fidelity, Pangram status, and authorship-signal retention. Pangram Human does not prove Joel's idiolect survived, and profile similarity does not prove fidelity or natural authorship.
- For substantial sectional or article-wide AI rewriting, compare the original and candidate against a held-out, genre-relevant corpus of genuine owner-authored or owner-edited-final work.
- A single-author comparison is a **retention proxy**, not IER. True IER requires a closed-set multi-author attribution benchmark with disjoint profile/evaluation material and aligned originals/rewrites.
- Do not install a universal pass threshold. Treat instrument/version, corpus, genre, boundary, baseline quality, and direction of movement as part of the result.
- Never add errors, autobiographical detail, catchphrases, unusual punctuation, or corpus tics merely to raise similarity. Metrics remain evidence; owner authority, meaning, and editorial quality control the prose.
- Keep private profile text out of reports. Preserve hashes, method version, sample/word counts, boundary identities, and aggregate measurements.

Operational protocol and commands: `docs/IDIOLECT-RETENTION-PROTOCOL.md`. Exact research translation and limitations: `state/IDIOLECT-ERASURE-RESEARCH-INTEGRATION-2026-08-17.md`.
