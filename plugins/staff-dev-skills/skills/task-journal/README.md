# Task Journal

Keep a local Markdown record of completed work and open tasks, with daily
close-out, recurring tasks, and monthly highlights.

## Use in Codex

Install the `staff-dev-skills` plugin using the
[repository installation instructions](../../../../README.md#install-locally),
then ask Codex to use `$task-journal`. For example:

- “Use $task-journal to record that I reviewed the cache migration RFC today.”
- “Add an open task to validate the canary rollout plan under Architecture.”
- “Add a daily recurring task to review service reliability metrics.”
- “Close out today's journal.”

Journals live in `~/journals`, with one file per month, such as
`October-2026.md`. Weeks and days appear only when they have entries. Category
headings are optional: tasks can go directly under a day. To group tasks, use
level-four headings within a day, with tasks directly underneath and no
blank line after the heading. The helper also removes existing blank or
whitespace-only lines after these headings when it saves a journal.

```markdown
# October 2026

## Highlights

- Aligned service teams on the cache migration design and rollout sequence.
- Improved incident readiness with updated runbooks and clear service ownership.

## Week 1 (09/28 to 10/04)

### Thursday

- [x] Mentored a senior engineer on design tradeoffs for the event pipeline

#### Architecture
- [x] Reviewed the cache migration RFC with service owners
- [ ] Validate the canary rollout plan and rollback criteria

#### Reliability
- [x] Updated the incident runbook and confirmed escalation ownership
- [ ] 🔁 Review service reliability metrics
```

## Task states and daily close-out

| Entry | Markdown |
| --- | --- |
| Completed work from a previous day | `- Documented event pipeline design tradeoffs` |
| Completed work today | `- [x] Reviewed the cache migration RFC` |
| Open work today | `- [ ] Validate the canary rollout plan` |
| Daily recurring task | `- [ ] 🔁 Review service reliability metrics` |

Closing a day converts checked tasks to regular bullets and moves unchecked
tasks to the next day, preserving their categories. Completed recurring tasks
also return as unchecked tasks on the next day. Empty categories are removed
from the closed day. Carry-forward works across month boundaries.

Close-out runs when requested; it is not scheduled automatically.

## Monthly highlights

At the start of a journal update, rollover checks earlier months whose
Highlights sections are empty. It moves their remaining open tasks to the
update date. Codex then reads those monthly journals and writes concise,
non-redundant highlights from completed work.

A populated Highlights section indicates that the month is finalized. Future
rollovers skip that month, and the helper refuses to overwrite its highlights.
No HTML comments or bookkeeping markers are added.

Closing the last day of a month carries tasks into the next month. The monthly
summary is generated during a subsequent update in the new month. The current
skill requires a highlights list; it does not require a broader analysis of
themes, blockers, or next-month priorities.

## Run the helper directly

The helper requires Python 3.10 or newer and uses only the standard library.
Run these commands from this skill's directory. The reference date makes the
dated examples reproducible; omit it when recording tasks for today.

```bash
python3 scripts/journal.py ensure-day --date 2026-10-01
python3 scripts/journal.py add --date 2026-10-01 --reference-date 2026-10-01 \
  --state current-done --text "Mentored a senior engineer on event pipeline design"
python3 scripts/journal.py add --date 2026-10-01 --reference-date 2026-10-01 \
  --state current-done --heading Architecture --text "Reviewed the cache migration RFC"
python3 scripts/journal.py add --date 2026-10-01 --reference-date 2026-10-01 \
  --state open --heading Architecture --text "Validate the canary rollout plan"
python3 scripts/journal.py add --date 2026-10-01 --reference-date 2026-10-01 \
  --state open --heading Reliability --text "🔁 Review service reliability metrics"
python3 scripts/journal.py list --date 2026-10-01
python3 scripts/journal.py close-day --date 2026-10-01
```

Omit `--heading` to add a task directly under the day, as in the first `add`
command above.

`rollover --date YYYY-MM-DD` prints JSON containing `unfinalized_months` and
`carried_tasks`. It does not write a summary itself. After reading a reported
month, supply each highlight to `finalize`, for example:

```bash
python3 scripts/journal.py finalize --month September-2026.md \
  --highlight "Aligned service teams on the cache migration design and rollout sequence."
```

Finalization requires at least one non-blank highlight. Use `update` and
`remove` with exact task text; inspect their options with `--help`.
For an alternate journal location or isolated testing, put
`--journal-dir /path/to/journals` before the subcommand.

The agent workflow is maintained in [SKILL.md](SKILL.md). From the repository
root, run the helper tests with `python3 -m unittest discover -s tests -v`.
