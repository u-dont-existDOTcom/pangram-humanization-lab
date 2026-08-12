# Live Smoke Report

Record each plane independently. A passing mocked or deterministic plane cannot be substituted for a live result.

| Plane | Status | Exact provider/model/version | Duration | Evidence/artifact | Limitation |
|---|---|---|---:|---|---|
| Claude CLI structured call | pending | | | | |
| Codex CLI structured call | pending | | | | |
| Pangram async auth probe (`GET /task/<sentinel>`, no task creation) | pending | required detector version 4.0 | | | valid auth is 200/403/404; 401 rejected key; 402 credits required |
| Pangram harmless submit | not run unless explicit | pangram-4 | | | consumes one task |
| Direct research fetch | pending | | | | plumbing only |
| Silent-child heartbeat | pending | local Python child | | | |

Do not record credentials. Pangram submission is opt-in even when the model-availability check is requested.
