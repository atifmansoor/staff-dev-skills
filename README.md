# Staff Dev Skills

A GitHub-shareable Codex marketplace containing reusable skills. The first
plugin bundle is `staff-dev-skills`, which includes `task-journal` and
`code-walkthrough`.

## Repository layout

```text
.agents/plugins/marketplace.json     # Repository marketplace catalog
plugins/staff-dev-skills/            # Installable plugin bundle
  skills/task-journal/               # Local monthly task journal
  skills/code-walkthrough/           # Guided evidence-based code review
```

## Install locally

Clone this repository, then run the following from its root:

```bash
codex plugin marketplace add "$(pwd)"
codex plugin add staff-dev-skills@personal
```

Start a new Codex task afterward so the bundled skills are available. The
plugin writes task journals only to `~/journals`, never into this repository.

## Task journal

Use `$task-journal` to record current open work, current completed work, and
completed work from earlier dates. It creates sparse monthly files such as
`~/journals/September-2026.md`, supports daily close-out, and creates
model-authored monthly highlights during rollover.

See the [task journal guide](plugins/staff-dev-skills/skills/task-journal/README.md)
for examples, task formatting, close-out behavior, and helper commands.

## Code walkthrough

Use `$code-walkthrough` to guide an evidence-based review of the current diff
or a named branch. It pauses after each review area so you can ask questions
before continuing, optionally retrieves a linked ticket through an available
MCP connector, groups changed files into digestible batches, and ends with
structured finding candidates and an approve/hold or push-readiness judgment.
Each file explanation includes syntax-highlighted Before/After excerpts or
resulting code, with the complete diff available for deeper inspection.

## Adding a skill

Create the new skill under `plugins/staff-dev-skills/skills/`, validate it, then
update the plugin version before reinstalling it in Codex.

## License

MIT. See [LICENSE](LICENSE).
