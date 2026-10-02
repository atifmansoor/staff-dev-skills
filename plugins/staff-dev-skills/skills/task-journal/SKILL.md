---
name: task-journal
description: "Maintain a local monthly task journal when logging completed work, open tasks, daily close-outs, or monthly highlights."
---

# Task Journal

Maintain markdown journals in `~/journals`, one `Month-YYYY.md` file per month.
Use `scripts/journal.py` for every deterministic journal edit. It defaults to
`~/journals`; pass `--journal-dir` only for an explicitly requested alternate
location or isolated testing.

Use this document structure for every journal the helper creates or updates:

```markdown
# Month YYYY

## Highlights

## Week N (MM/DD to MM/DD)

### Monday
```

Keep weeks and day sections sparse: create them only when an entry or carried
task needs that date.

## Task updates

Interpret natural-language task requests, including non-exact references to an
existing task. Resolve that ambiguity yourself, then pass an exact date and
task text to the helper. Do not ask the helper to fuzzy-match task text.

The task format is date-sensitive and must be preserved exactly:

- A completed task recorded for a prior day is a regular bullet: `- task`.
- A completed task recorded for the current day is a checked task: `- [x] task`.
- An open task recorded for the current day is an unchecked task: `- [ ] task`.

For a completed task on a previous date, use `add --state completed`; do not
use a checked checkbox. For current-date entries, use `current-done` or `open`.
The helper rejects current-day checkbox states when their date differs from its
reference date.

Use `update`, `remove`, and `list` only after identifying an exact matching
task. If more than one exact task exists, identify the intended entry before
editing it.

## Category headings

Within a day, use H4 category headings such as `#### Interview prep`. Place
tasks directly beneath these headings, without blank or whitespace-only lines.
When a user adds a task under a named category, pass that title through `add --heading`
without the markdown hashes. When closing a day, the helper preserves each
carried task's nearest H4 heading, creates that heading on the next day if
needed, and adds the task beneath it. Completed tasks remain under their
original heading in the closed day. The same heading preservation applies when
open tasks roll into a new month. When close-out leaves an H4 heading with no
non-blank content, remove that empty heading.

## Recurring tasks

Mark a daily recurring task with the exact leading text `🔁 ` after its task
checkbox or bullet, for example `- [ ] 🔁 Review job leads`. The prefix is the
only recurring marker; do not use `***`, suffix markers, or a differently
placed emoji.

When closing a day, a completed recurring task becomes a regular bullet in
that day's journal and is also added as an open recurring task on the next
day. An open recurring task already follows the normal carry-forward behavior.

## Daily close-out and rollover

When asked to close out a day, run `close-day --date YYYY-MM-DD`. It changes
checked tasks into regular bullets and moves unchecked tasks to the next date.

At the start of a journal update, run `rollover --date YYYY-MM-DD`. For each
unfinalized earlier month it moves all remaining unchecked tasks to the active
date and reports the affected monthly files. Read each reported file, create a
concise, non-redundant Highlights list from its completed work, and finalize it
with one `finalize --month FILE --highlight TEXT` argument per highlight. The
model writes the summary; the helper only writes supplied text. Then create or
update the active month/day as needed.

A month is finalized when its Highlights section has content. The helper skips
those months during rollover and refuses to overwrite their highlights. Supply
at least one non-blank highlight when finalizing. Keep journals plain Markdown;
do not add HTML comments or bookkeeping markers.

Weeks are sparse and created only for dates that receive entries. They use the
calendar's Monday-Sunday range and the calendar-week number for that month.

## Helper examples

```bash
# Create the monthly journal and today's day section when needed.
python3 scripts/journal.py ensure-day --date 2026-09-15

# Add current-day task states.
python3 scripts/journal.py add --date 2026-09-15 --state current-done --text "Shipped the release"
python3 scripts/journal.py add --date 2026-09-15 --state open --text "Review customer feedback"
python3 scripts/journal.py add --date 2026-09-15 --state current-done --text "🔁 Review job leads"
python3 scripts/journal.py add --date 2026-09-15 --state open --heading "Interview prep" --text "Practice coding questions"

# Add completed work to a prior day as a normal bullet.
python3 scripts/journal.py add --date 2026-09-14 --state completed --text "Prepared release notes"
```
