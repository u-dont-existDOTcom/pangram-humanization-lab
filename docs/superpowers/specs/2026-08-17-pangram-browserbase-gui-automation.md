# Pangram Browserbase GUI Automation Specification

## Goal

Automate Joel's current manual Pangram GUI workflow while the Pangram API credential path is unreliable: reuse a logged-in cloud browser, submit exact hash-bound article boundaries, preserve Pangram's GUI/PDF evidence, and refuse duplicate completed measurements by default.

## Authority and safety

- This subsystem measures text. It never edits article prose or changes article authority.
- Exact input bytes are identified by SHA-256 before browser work begins.
- A completed GUI result for the same input SHA and GUI runner version is reused unless `--force` is explicitly supplied.
- Browserbase API credentials and Pangram authentication state must never be committed.
- Pangram cookies/authentication live only inside a Browserbase persistent Context.
- Browserbase Context IDs are supplied through environment/secret configuration or the local ignored bootstrap file, not embedded in article prose or detector result files.
- GUI automation is secondary detector evidence under the existing Pangram lab rules.

## Browser architecture

Use Browserbase cloud Chromium sessions controlled by Playwright over CDP. Browserbase's REST API creates sessions and returns `connectUrl`; Browserbase Contexts persist Pangram login cookies across sessions. The runner uses the default recorded Browserbase browser context rather than launching a local browser.

Browserbase resolves the project from the API key; this subsystem does not request, store, or set `BROWSERBASE_PROJECT_ID`.

Environment variables:

- `BROWSERBASE_API_KEY` — required.
- `BROWSERBASE_CONTEXT_ID` — required for unattended GitHub Actions runs; optional locally when bootstrap has saved the Context ID under `~/.config/pangram-gui/`.
- `PANGRAM_GUI_URL` — optional override; default `https://www.pangram.com/dashboard`.

No Pangram password is stored in GitHub. The initial login is performed manually in Browserbase's live debugger once, then persisted in the Context.

## Commands

### Bootstrap login

`python scripts/pangram_gui_browserbase.py bootstrap`

Behavior:

1. Create a Browserbase Context from the API key if no context ID is supplied.
2. Start a Browserbase session with Context persistence enabled and keep-alive long enough for manual login.
3. Open `https://www.pangram.com/login`.
4. Print the Browserbase live debugger URL and Context ID.
5. Wait for the user to complete Pangram login in the live debugger and confirm locally.
6. Navigate to Pangram's authenticated `/dashboard`, reject login/signup routes or a visible account wall, verify that a detector text input is available, then close the browser so Context changes persist.
7. Save the non-secret Context ID to `~/.config/pangram-gui/browserbase-context-id` for automatic local reuse.

### Run measurements

`python scripts/pangram_gui_browserbase.py run --input <path> [--input <path> ...]`

Default Romance invocation uses:

- `work/romance-current-assembly/pangram-part-1.txt`
- `work/romance-current-assembly/pangram-part-2.txt`

For each input:

1. Compute exact SHA-256 and word count.
2. Reuse a completed result if the measurement identity already exists, unless forced. Refuse an automatic repeat when a prior failure says a detector submission may already have occurred.
3. Navigate to Pangram's authenticated `/dashboard` in the persistent Context and fail before filling text if login/signup is visible.
4. Find the visible text input using a bounded selector strategy (`textarea`, contenteditable textbox, generic textbox role).
5. Fill exact text bytes as Unicode text; no labels or test metadata are added to submitted copy.
6. Find and activate the visible Pangram detection action using bounded button-name patterns.
7. Wait for the report UI (`Authorship Breakdown` / analyzed result markers).
8. Extract body text and parse overall Human/AI/AI-assisted fractions plus segment label, word count, confidence, and segment text where the GUI exposes them.
9. Save machine-readable JSON and GUI evidence.
10. Prefer Pangram's native PDF/report download when a clearly named PDF/download control exists; otherwise save a Playwright Chromium print-to-PDF fallback and mark it as fallback provenance.
11. Save the Browserbase session ID and recording/debug URL for reproducibility.

## Result layout

Each measurement is stored under:

`state/gui-runs/pangram-4/<input_sha256>/`

Expected artifacts:

- `result.json` — structured metadata, parsed summary, parsed segments, exact input hash/word count, session ID, runner version, completion status.
- `report.pdf` — native Pangram PDF when available, otherwise a clearly marked browser-print fallback.
- `report-body.txt` — raw visible report text used for deterministic parsing.
- `failure.json` and `failure.png` — only on failed runs, with session/debug URL and failure stage.

The runner must never claim a native Pangram PDF when the artifact came from Playwright printing.

## Parser contract

The parser accepts raw GUI body text and must tolerate separators/newlines changing while retaining exact detected segment text. It extracts:

- overall `fraction_human`, `fraction_ai`, `fraction_moderately_ai_assisted`, `fraction_lightly_ai_assisted` when shown;
- segment label in `{Human Written, Fully AI Generated, Moderately AI Assisted, Lightly AI Assisted}`;
- integer word count;
- confidence in `{High, Medium, Low}` when shown;
- text from each segment header to the next segment header.

Missing fields are represented as `null` rather than invented.

## GitHub Actions

Add a manual `workflow_dispatch` workflow that:

- requires repository secrets `BROWSERBASE_API_KEY` and `BROWSERBASE_CONTEXT_ID`;
- installs the optional browser dependency;
- runs the two current Romance Pangram halves by default;
- commits only newly created GUI result artifacts back to the exact branch;
- never creates or updates the Browserbase Context automatically;
- fails closed when login has expired or the Pangram UI cannot be located.

## Non-goals

- No autonomous AI browser agent.
- No CAPTCHA bypass logic.
- No storage of Pangram email/password.
- No detector-driven article rewriting.
- No silent selector fallback that clicks arbitrary buttons.
- No duplicate completed or ambiguous post-submit measurements unless explicitly forced after evidence review.
