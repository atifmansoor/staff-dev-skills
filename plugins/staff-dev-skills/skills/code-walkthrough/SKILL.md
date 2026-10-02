---
name: code-walkthrough
description: Guide an evidence-based, step-by-step walkthrough of a current Git diff or named branch, including requirements, design, testing, risks, and a final review judgment.
---

# Code Walkthrough

Lead an interactive code review that helps a user understand a change before approval or pushing it. This is a review workflow: do not edit code, post pull request comments, or change the checked-out branch.

## Start the review

Begin by asking the user to choose exactly one review source:

- **Current diff**: review the staged and unstaged tracked changes relative to `HEAD`.
- **Named branch**: provide the branch that contains the changes to review.

Also ask for an optional JIRA-like ticket link and whether the outcome is for a pull request or for deciding whether to push a branch. Do not begin a numbered walkthrough step until the user answers.

For a current diff, collect repository status and the complete diff from `HEAD`. For a named branch, resolve its remote when possible, fetch it when it is not available locally or the user asked to pull it, calculate its merge base, and inspect the change from that merge base to the named branch. Never check out, merge, rebase, reset, or otherwise alter the user's worktree.

When a ticket link is supplied, use the matching configured MCP connector to retrieve it. Capture the ticket identifier, title, description, acceptance criteria, and relevant linked context for step 1. Do not replace MCP retrieval with web research or invent missing ticket content. If no matching connector is available or retrieval fails, disclose the reason in the review and continue from repository evidence.

Ground conclusions in ticket, code, and test evidence, while clearly labeling inferences and missing evidence. Never turn an absence of evidence into a pass. Refer to a file, ticket, or test command directly when that context helps; do not use synthetic evidence IDs or trailing marker references.

## Paused walkthrough contract

Produce only one walkthrough section at a time. At the end of every section, say `Reply next to continue, or ask a question about this step.` Then stop.

- Advance only when the user says `next` or an unambiguous equivalent.
- Answer a question about the paused section without advancing; repeat the continuation prompt afterward.
- Resume from the exact unfinished section after any question.
- If new information changes earlier conclusions, explicitly note the affected earlier step before continuing.

Use the following numbered sections in order.

## 1. Requirements and acceptance criteria

State the problem being solved, how the proposed solution addresses it, and a testable acceptance-criteria list. Prefer the retrieved ticket; otherwise derive cautiously from the diff and surrounding code, marking the result as inference. Identify requirements that remain unknown.

After the acceptance criteria, include a compact evidence map only when it materially improves the walkthrough—for example, when a ticket, a large diff, and multiple test artifacts need to be distinguished. Keep it in this step only. Use readable source labels such as `Ticket`, `Code`, `Tests`, and `Inference`; do not assign IDs, cite the map from later steps, or append its references to flow or design bullets.

## 2. Test evidence

Summarize changed tests, relevant existing tests, CI artifacts, and test logs. When the project exposes clear, targeted, safe test commands, run the smallest relevant commands and report the exact command and result. Do not install dependencies, access production systems, or run destructive commands merely to produce evidence. If no appropriate test can be run, say why and identify the missing evidence.

## 3. Code design

Explain the important components, responsibilities, data ownership, and interfaces changed by the diff. Include a Mermaid class diagram for meaningful type/component relationships and a Mermaid sequence diagram for meaningful multi-party interactions. Omit either diagram when it would not clarify the design, and state why rather than adding a decorative diagram.

## 4. Affected end-to-end flow

Explain one representative affected journey from trigger through its observable result, including error or alternate handling where it matters. Always include a Mermaid `flowchart` that matches the described flow and identifies changed components. Use a plain numbered narrative for the flow; do not append evidence markers or reference tags to individual steps.

## 5. Changed-file walkthrough

Order all changed files by their logical role in the affected flow. Present two or three files per response (the final group may contain one), and give every changed file exactly once. Treat each group as a paused substep—`5.1`, `5.2`, and so on—before moving to step 6.

Inspect the complete diff for every file, but present the code needed to understand the change rather than every patch line. For each file:

1. Give its path and lead with what changed, why it matters, and its role in the affected flow.
2. Show concise code excerpts inline in fenced blocks labeled with the actual language, such as `typescript`, `sql`, or `python`, so the app can apply syntax highlighting. For modified logic, label paired excerpts **Before** and **After**. For new files or additions, show the resulting code; for deletions, show the relevant removed code and explain the behavior that disappears.
3. Explain subtle behavior and any review concern immediately below the relevant excerpt.

Use actual code from the reviewed revisions, retain enough surrounding context to understand it, and identify separate excerpts when intervening code is omitted. Do not include patch headers or added/removed line prefixes in language-labeled blocks. Cover all meaningful changes in the explanation even when only selected excerpts are displayed. For binary files, pure renames, or mechanical changes that do not benefit from code excerpts, explain the change directly.

Keep the two- or three-file batches and pause after each group. Make the complete diff available for deeper inspection through the app's native review pane when it can show the selected review scope, or through a link to the exact PR/file diff or a patch artifact. This supplements the inline explanation and code; it does not replace them. Show a raw `diff` block only if the user asks for the full patch.

## 6. Correctness and behavior

Compare the implementation against every known requirement and acceptance criterion. State whether each is satisfied, contradicted, or unproven, with evidence. Surface behavior changes, edge cases, and failure paths.

## 7. Test coverage and gaps

Evaluate coverage of the accepted behavior, failures, boundaries, and regressions. Separate missing automated tests from scenarios that cannot be verified from available evidence. Recommend the smallest high-value additions.

## 8. Performance and scale

Assess changed hot paths, query/network patterns, allocations, concurrency, and scale-sensitive work. Identify supported risks, explain assumptions, and call out when performance cannot be assessed without profiling or production data.

## 9. Readability and maintainability

Assess naming, cohesion, control flow, duplication, coupling, documentation, and consistency with nearby code. Focus on concrete maintainability outcomes, not stylistic preferences.

## 10. Security and compliance

Assess changed inputs, authorization, secrets, sensitive data, dependency and license implications, logging, and relevant repository policies. State whether each concern was inspected, not applicable, or unverified; do not claim a full security audit from a diff review.

## 11. Review comments

Present only actionable findings as candidates; do not post them. For each, use this structure:

```markdown
### [P0-P3] Short finding title
- Location: `path/to/file:line` (or `general` when no precise location exists)
- Evidence: ...
- Impact: ...
- Suggested resolution: ...
- Candidate action: PR comment | ask coding agent to fix
```

Use P0 for blocking, immediate harm; P1 for serious correctness, security, or release risk; P2 for meaningful but non-blocking risk; and P3 for a worthwhile minor improvement. Do not manufacture comments merely to populate this step.

## 12. Checklist and final judgment

Give a concise checklist of all review areas with `Pass`, `Concern`, `Unverified`, or `Not applicable`, citing outstanding finding IDs where useful. For a pull request, conclude `Approve` only when no blocking concerns or unverified acceptance criteria remain; otherwise conclude `Hold`. For a branch that has not been pushed, conclude either `Ready to push` or `Fix before pushing`. Tie the judgment to the directly stated requirements, tests, and findings, then list the minimum actions needed to change a hold/fix decision.
