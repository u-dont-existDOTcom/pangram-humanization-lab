# Hands-Off Controller Plan Index

The approved design is implemented as two independently testable releases.

1. [`2026-08-13-local-hands-off-controller.md`](2026-08-13-local-hands-off-controller.md) removes the repeated Zorin terminal loop. It installs from one command, verifies and accepts trusted fast-forward updates, preserves `.state`, interprets typed child outcomes, repairs outer-controller failures, and resumes the exact thread.
2. [`2026-08-13-remote-rescue-watch.md`](2026-08-13-remote-rescue-watch.md) adds the privacy-safe repair capsule and hourly GitHub rescue watch. It is deliberately second: remote repair must not become the normal scheduler or a substitute for local verification.

Execute the plans in that order. The first plan is releasable by itself and must pass its target-machine acceptance before the remote rescue branch is allowed to write to the stable install channel.
