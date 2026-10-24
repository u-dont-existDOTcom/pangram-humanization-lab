# Pangram matched pair: frozen selection before calls

Task: test whether literal successful rewrite examples increase Human classification **without Emulate at inference time**. This compares two independently generated GPT-6.1 Sol High outputs for the *same held-out somatic paragraph*, after separate fresh-context generation.

## Candidates (exact text identities)

- **A: no-exemplar baseline**, SHA-256 `6ecfa7f28d8cbefd3150d29dba35543f0dec60ba1ca568a365f19955a65fff9b`, 95 words. Fresh blind reviewer: fidelity PASS, naturalness 4/5, preference rank **1 of 3** for this target.
- **C: positive-demo trained**, SHA-256 `18d0845a33c83b1efbe5aad7cd16fc4c9736649fab480e310e08d9061368c20e`, 102 words. Fresh blind reviewer: fidelity PASS, naturalness 4/5, preference rank **2 of 3**, with a mildly clunky opening. Two training pairs were exposed before generation; **no Emulate call or output for this target** was available to the writer.
- **B: causal-plan only**, reviewer rank 3 and a source emphasis shift, **not sent to Pangram**.

The four relevant candidates in the pilot that received PASS from the blind reader are A/C on both targets; the detector budget is intentionally limited to this one *matched target pair* to avoid conflating topic, length and condition.

## Explicit prediction before paid scans

Based on independent naturalness judgments, predict that **baseline A will be at least as Human as treatment C** on Pangram 4.1, but both could pass Human or fail because detector classifications are not authorial truth. A consistently stronger treatment would contradict the blind reader ordering and indicate a detector-versus-reader objective conflict, not by itself proven learning.

The user retains final voice/meaning judgment. Only source-preserving outputs count. The older historical somatic model-Human labels were under a different boundary/date and aren't current calibration.

## Budget and transport

Maximum **two new GUI submissions**, exactly the A and C input SHA files above. Guarded `pangram-local` uses the dedicated authenticated Brave profile on Joel's machine. The older HTML report marker is stale for Pangram 4.1, so if it flags timeout, **recover the exact stored History record and its authoritative `response.overall` fields by input bytes and reservation timestamp**; do not resubmit or guess based on `prediction_prob`. Append a recovery note; no article master changes.

Stopping gate: after this pair, analyze A vs B vs C, not further same-method prompt variants. Do not promote the T1/T2 generation skill without new owner-approved generalization to a second rhetorical job.
