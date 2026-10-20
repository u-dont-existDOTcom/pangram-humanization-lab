# Owner correction — six hypothesis-gated Pangram tries per paragraph — 2026-10-20

Status: **ACTIVE direct owner production rule**. The normative policy is in `joel-articles/docs/PANGRAM-PRODUCTION-BUDGET-20261020.md`; this note records the lab execution binding.

Joel clarified: sometimes fixing one red sentence causes a different sentence to turn red in Pangram 4.1, so the previous two-try limit is too restrictive. Permit **at most six new detector submissions per paragraph**, but only while the worker has a specific, credible idea of what needs fixing next. Six is a hard ceiling, never a default number of tries.

- Before the initial submission and every subsequent one, log the exact paragraph, current sentence shading, Human/AI prediction, protected meaning, and expected outcome.
- To justify the next submission, identify the exact failing sentence or surrounding structure, why it seems model-shaped, the concrete planned change, and a specific prediction that this repair addresses the observed cause. A newly exposed red sentence is a genuinely distinct target **within the same paragraph**; it does not reset the attempt count.
- Stop immediately and ask Joel for help if no substantive credible next hypothesis remains, even when fewer than six checks have occurred. Two successive unexplained predictions about the *same unresolved defect* require escalation; explained changes that reveal new sentences may continue within the unreset six-attempt ceiling.

- Count all potentially billable requests across versions, transports, workers and chats; an ambiguous submission uses a slot pending recovery. The previous six-call *section* limit is historical where it conflicts with independent paragraph repair. Section certification remains limited to one initial check and one justified recheck.
- Keep work to one section or about five paragraphs. Do not repeatedly test the entire section during edits; reserve whole-article checks for final readiness. Dark green is the preferred sentence-level target, without sacrificing meaning or voice.

- The earlier Pangram 4.1 GUI submission for the community paragraph remains unresolved, and the last authenticated account view showed no remaining credits. Changing this limit does **not** permit retrying a potentially charged request or proceeding without a valid spending preflight.

This is a direct project-specific owner correction, not a measured claim about detector accuracy. Capture its source hash and ledger disposition. No Pangram submissions were conducted to establish this rule.
