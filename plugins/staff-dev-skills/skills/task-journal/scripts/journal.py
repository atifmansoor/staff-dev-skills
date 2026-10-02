#!/usr/bin/env python3
"""Deterministic markdown operations for the task-journal skill."""

from __future__ import annotations

import argparse
import calendar
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

WEEKDAYS = tuple(calendar.day_name)
WEEK_RE = re.compile(r"^## Week (\d+) \((\d{2}/\d{2}) to (\d{2}/\d{2})\)$")
DAY_RE = re.compile(r"^### (Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)$")
SUBHEADING_RE = re.compile(r"^#### (?P<title>.+)$")
TASK_RE = re.compile(r"^- (?:\[(?P<state>[ xX])\] )?(?P<text>.+)$")
RECURRING_PREFIX = "🔁 "
MONTH_RE = re.compile(r"^([A-Za-z]+)-(\d{4})\.md$")


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("dates must use YYYY-MM-DD") from error


def journal_dir(value: str | None) -> Path:
    return Path(value).expanduser() if value else Path.home() / "journals"


def month_path(root: Path, day: date) -> Path:
    return root / f"{day.strftime('%B-%Y')}.md"


def read_lines(path: Path, month: date | None = None) -> list[str]:
    if not path.exists():
        if month is None:
            month = month_from_path(path)
        if month is None:
            raise ValueError(f"cannot infer a month from {path.name}")
        return [f"# {month:%B %Y}", "", "## Highlights", ""]
    return path.read_text(encoding="utf-8").splitlines()


def write_lines(path: Path, lines: list[str]) -> None:
    formatted = []
    after_subheading = False
    for line in lines:
        if after_subheading and not line.strip():
            continue
        formatted.append(line)
        after_subheading = bool(SUBHEADING_RE.match(line))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(formatted).rstrip() + "\n", encoding="utf-8")


def week_details(day: date) -> tuple[int, date, date]:
    first = day.replace(day=1)
    first_monday = first - timedelta(days=first.weekday())
    monday = day - timedelta(days=day.weekday())
    return ((monday - first_monday).days // 7 + 1, monday, monday + timedelta(days=6))


def week_header(day: date) -> str:
    number, monday, sunday = week_details(day)
    return f"## Week {number} ({monday:%m/%d} to {sunday:%m/%d})"


def week_bounds(lines: list[str], header: str) -> tuple[int, int] | None:
    try:
        start = lines.index(header)
    except ValueError:
        return None
    end = next((i for i in range(start + 1, len(lines)) if WEEK_RE.match(lines[i])), len(lines))
    return start, end


def ensure_day(lines: list[str], day: date) -> tuple[int, int]:
    """Ensure a dated weekday section and return its content bounds."""
    header = week_header(day)
    bounds = week_bounds(lines, header)
    if bounds is None:
        number, _, _ = week_details(day)
        insertion = len(lines)
        for index, line in enumerate(lines):
            match = WEEK_RE.match(line)
            if match and int(match.group(1)) > number:
                insertion = index
                break
        block = ([""] if insertion and lines[insertion - 1] else []) + [header, ""]
        lines[insertion:insertion] = block
        bounds = week_bounds(lines, header)
        assert bounds is not None

    start, end = bounds
    weekday = WEEKDAYS[day.weekday()]
    day_indexes = [
        (i, WEEKDAYS.index(DAY_RE.match(lines[i]).group(1)))
        for i in range(start + 1, end)
        if DAY_RE.match(lines[i])
    ]
    for index, weekday_number in day_indexes:
        if weekday_number == day.weekday():
            next_index = next((i for i, _ in day_indexes if i > index), end)
            return index + 1, next_index

    insertion = next((i for i, weekday_number in day_indexes if weekday_number > day.weekday()), end)
    block = ([""] if insertion > start + 1 and lines[insertion - 1] else []) + [f"### {weekday}", ""]
    lines[insertion:insertion] = block
    return ensure_day(lines, day)


def render_task(text: str, state: str) -> str:
    return {"open": f"- [ ] {text}", "current-done": f"- [x] {text}", "completed": f"- {text}"}[state]


def is_recurring(text: str) -> bool:
    """Return whether task text uses the journal's explicit recurring prefix."""
    return text.startswith(RECURRING_PREFIX)


def task_entries(lines: list[str], start: int, end: int) -> list[tuple[int, str, str | None]]:
    found = []
    for index in range(start, end):
        match = TASK_RE.match(lines[index])
        if match:
            found.append((index, match.group("text"), match.group("state")))
    return found


def task_entries_with_headings(
    lines: list[str], start: int, end: int
) -> list[tuple[int, str, str | None, str | None]]:
    """List day tasks together with their nearest H4 category heading."""
    heading = None
    found = []
    for index in range(start, end):
        subheading = SUBHEADING_RE.match(lines[index])
        if subheading:
            heading = subheading.group("title")
            continue
        match = TASK_RE.match(lines[index])
        if match:
            found.append((index, match.group("text"), match.group("state"), heading))
    return found


def open_tasks_with_headings(lines: list[str]) -> list[tuple[int, str, str | None]]:
    """List unchecked tasks from a month together with their day-local H4 heading."""
    heading = None
    found = []
    for index, line in enumerate(lines):
        if WEEK_RE.match(line) or DAY_RE.match(line):
            heading = None
            continue
        subheading = SUBHEADING_RE.match(line)
        if subheading:
            heading = subheading.group("title")
            continue
        match = TASK_RE.match(line)
        if match and match.group("state") == " ":
            found.append((index, match.group("text"), heading))
    return found


def prune_empty_subheadings(lines: list[str], start: int, end: int) -> None:
    """Remove H4 headings whose section has no non-blank content."""
    index = start
    while index < end:
        if not SUBHEADING_RE.match(lines[index]):
            index += 1
            continue
        next_heading = next(
            (next_index for next_index in range(index + 1, end) if SUBHEADING_RE.match(lines[next_index])),
            end,
        )
        if all(not line.strip() for line in lines[index + 1:next_heading]):
            del lines[index:next_heading]
            end -= next_heading - index
        else:
            index = next_heading


def enforce_current_state(day: date, state: str, reference: date) -> None:
    if state in {"open", "current-done"} and day != reference:
        raise ValueError(f"{state} is only valid for the reference/current day ({reference})")


def task_insertion_index(lines: list[str], start: int, end: int, heading: str | None) -> int:
    """Return where a task should be added, creating a requested H4 heading."""
    if heading is None:
        return end
    target = f"#### {heading}"
    for index in range(start, end):
        if lines[index] == target:
            return next(
                (next_index for next_index in range(index + 1, end) if SUBHEADING_RE.match(lines[next_index])),
                end,
            )
    block = ([""] if end > start + 1 and lines[end - 1] else []) + [target]
    lines[end:end] = block
    return end + len(block)


def add_task(
    root: Path,
    day: date,
    text: str,
    state: str,
    reference: date,
    heading: str | None = None,
) -> None:
    enforce_current_state(day, state, reference)
    path = month_path(root, day)
    lines = read_lines(path, day)
    start, end = ensure_day(lines, day)
    lines.insert(task_insertion_index(lines, start, end, heading), render_task(text, state))
    write_lines(path, lines)


def exact_task(lines: list[str], day: date, text: str) -> tuple[int, int]:
    start, end = ensure_day(lines, day)
    matches = [(index, state) for index, task, state in task_entries(lines, start, end) if task == text]
    if len(matches) != 1:
        qualifier = "no" if not matches else "multiple"
        raise ValueError(f"{qualifier} exact matches for task: {text!r}")
    return matches[0]


def update_task(root: Path, day: date, match: str, replacement: str, state: str | None, reference: date) -> None:
    path = month_path(root, day)
    lines = read_lines(path, day)
    index, old_state = exact_task(lines, day, match)
    chosen = state or ({" ": "open", "x": "current-done", "X": "current-done"}.get(old_state, "completed"))
    enforce_current_state(day, chosen, reference)
    lines[index] = render_task(replacement, chosen)
    write_lines(path, lines)


def remove_task(root: Path, day: date, text: str) -> None:
    path = month_path(root, day)
    lines = read_lines(path, day)
    index, _ = exact_task(lines, day, text)
    del lines[index]
    write_lines(path, lines)


def list_tasks(root: Path, day: date) -> None:
    path = month_path(root, day)
    if not path.exists():
        print("[]")
        return
    lines = read_lines(path, day)
    start, end = ensure_day(lines, day)
    result = [
        {
            "text": text,
            "state": {None: "completed", "x": "current-done", "X": "current-done", " ": "open"}[state],
            "heading": heading,
        }
        for _, text, state, heading in task_entries_with_headings(lines, start, end)
    ]
    print(json.dumps(result, indent=2))


def close_day(root: Path, day: date) -> None:
    source = month_path(root, day)
    lines = read_lines(source, day)
    start, end = ensure_day(lines, day)
    carry = []
    for index, text, state, heading in reversed(task_entries_with_headings(lines, start, end)):
        if state == " ":
            carry.append((text, heading))
            del lines[index]
        elif state in {"x", "X"}:
            lines[index] = f"- {text}"
            if is_recurring(text):
                carry.append((text, heading))
    start, end = ensure_day(lines, day)
    prune_empty_subheadings(lines, start, end)
    write_lines(source, lines)
    next_day = day + timedelta(days=1)
    for text, heading in reversed(carry):
        add_task(root, next_day, text, "open", next_day, heading)


def month_from_path(path: Path) -> date | None:
    match = MONTH_RE.match(path.name)
    if not match:
        return None
    try:
        return datetime.strptime(f"{match.group(1)} {match.group(2)}", "%B %Y").date()
    except ValueError:
        return None


def has_highlights(lines: list[str]) -> bool:
    """Treat a populated Highlights section as a completed monthly summary."""
    try:
        start = lines.index("## Highlights")
    except ValueError:
        return False
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return any(line.strip() for line in lines[start + 1:end])


def rollover(root: Path, active_day: date) -> None:
    active_month = active_day.replace(day=1)
    unfinalized = []
    carried = []
    for path in sorted(root.glob("*-????.md")):
        month = month_from_path(path)
        if month is None or month >= active_month:
            continue
        lines = read_lines(path, month)
        if has_highlights(lines):
            continue
        for index, text, heading in reversed(open_tasks_with_headings(lines)):
            carried.append((text, heading))
            del lines[index]
        write_lines(path, lines)
        unfinalized.append(path.name)
    for text, heading in reversed(carried):
        add_task(root, active_day, text, "open", active_day, heading)
    print(json.dumps({"unfinalized_months": unfinalized, "carried_tasks": [text for text, _ in reversed(carried)]}, indent=2))


def finalize(root: Path, month_name: str, highlights: list[str]) -> None:
    path = root / month_name
    if not path.exists():
        raise ValueError(f"month file does not exist: {month_name}")
    lines = read_lines(path, month_from_path(path))
    if has_highlights(lines):
        raise ValueError(f"month is already finalized: {month_name}")
    if not highlights or any(not item.strip() for item in highlights):
        raise ValueError("provide at least one non-blank highlight")
    try:
        start = lines.index("## Highlights")
    except ValueError as error:
        raise ValueError(f"missing Highlights section: {month_name}") from error
    end = next((i for i in range(start + 1, len(lines)) if WEEK_RE.match(lines[i])), len(lines))
    body = ["## Highlights", ""] + [f"- {item}" for item in highlights] + [""]
    lines[start:end] = body
    write_lines(path, lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--journal-dir", help="defaults to ~/journals")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("ensure-month", "ensure-day", "close-day", "rollover", "list"):
        command = sub.add_parser(name)
        command.add_argument("--date", type=parse_date, required=True)
    add = sub.add_parser("add")
    add.add_argument("--date", type=parse_date, required=True)
    add.add_argument("--text", required=True)
    add.add_argument("--state", choices=("open", "current-done", "completed"), required=True)
    add.add_argument("--heading", help="H4 category heading for this task, without markdown hashes")
    add.add_argument("--reference-date", type=parse_date, default=date.today())
    update = sub.add_parser("update")
    update.add_argument("--date", type=parse_date, required=True)
    update.add_argument("--match", required=True)
    update.add_argument("--replacement", required=True)
    update.add_argument("--state", choices=("open", "current-done", "completed"))
    update.add_argument("--reference-date", type=parse_date, default=date.today())
    remove = sub.add_parser("remove")
    remove.add_argument("--date", type=parse_date, required=True)
    remove.add_argument("--text", required=True)
    final = sub.add_parser("finalize")
    final.add_argument("--month", required=True)
    final.add_argument("--highlight", action="append", default=[])
    args = parser.parse_args()
    root = journal_dir(args.journal_dir)
    try:
        if args.command == "ensure-month":
            path = month_path(root, args.date)
            write_lines(path, read_lines(path, args.date))
        elif args.command == "ensure-day":
            path = month_path(root, args.date)
            lines = read_lines(path, args.date)
            ensure_day(lines, args.date)
            write_lines(path, lines)
        elif args.command == "add":
            add_task(root, args.date, args.text, args.state, args.reference_date, args.heading)
        elif args.command == "update":
            update_task(root, args.date, args.match, args.replacement, args.state, args.reference_date)
        elif args.command == "remove":
            remove_task(root, args.date, args.text)
        elif args.command == "list":
            list_tasks(root, args.date)
        elif args.command == "close-day":
            close_day(root, args.date)
        elif args.command == "rollover":
            rollover(root, args.date)
        elif args.command == "finalize":
            finalize(root, args.month, args.highlight)
    except ValueError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    sys.exit(main())
