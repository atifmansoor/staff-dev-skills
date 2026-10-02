"""End-to-end checks for the task-journal helper CLI."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/staff-dev-skills/skills/task-journal/scripts/journal.py"


class TaskJournalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.journals = Path(self.directory.name)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def run_journal(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--journal-dir", str(self.journals), *arguments],
            check=True,
            text=True,
            capture_output=True,
        )

    def month(self, name: str) -> str:
        return (self.journals / name).read_text(encoding="utf-8")

    def test_task_states_and_calendar_week_number(self) -> None:
        current = "2026-09-15"
        self.run_journal("add", "--date", "2026-09-14", "--state", "completed", "--text", "Prepared notes")
        self.run_journal("add", "--date", current, "--state", "current-done", "--text", "Released feature", "--reference-date", current)
        self.run_journal("add", "--date", current, "--state", "open", "--text", "Review feedback", "--reference-date", current)

        journal = self.month("September-2026.md")
        self.assertIn("# September 2026\n\n## Highlights", journal)
        self.assertIn("## Week 3 (09/14 to 09/20)", journal)
        self.assertIn("### Monday\n\n- Prepared notes", journal)
        self.assertIn("### Tuesday\n\n- [x] Released feature\n- [ ] Review feedback", journal)

    def test_close_day_converts_done_and_carries_open_across_month(self) -> None:
        current = "2026-09-30"
        self.run_journal("add", "--date", current, "--state", "current-done", "--text", "Published changelog", "--reference-date", current)
        self.run_journal("add", "--date", current, "--state", "current-done", "--text", "🔁 Review job leads", "--heading", "Interview prep", "--reference-date", current)
        self.run_journal("add", "--date", current, "--state", "open", "--text", "Plan next sprint", "--heading", "High-value admin / pipeline", "--reference-date", current)
        self.run_journal("close-day", "--date", current)

        september = self.month("September-2026.md")
        october = self.month("October-2026.md")
        self.assertIn("- Published changelog", september)
        self.assertNotIn("[x] Published changelog", september)
        self.assertIn("- 🔁 Review job leads", september)
        self.assertNotIn("[x] 🔁 Review job leads", september)
        self.assertNotIn("Plan next sprint", september)
        self.assertNotIn("#### High-value admin / pipeline", september)
        self.assertIn("## Week 1 (09/28 to 10/04)", october)
        self.assertIn("### Thursday\n\n#### Interview prep\n- [ ] 🔁 Review job leads", october)
        self.assertIn("#### High-value admin / pipeline\n- [ ] Plan next sprint", october)

    def test_close_day_prunes_manual_empty_category_headings(self) -> None:
        journal = self.journals / "September-2026.md"
        journal.write_text(
            "# September 2026\n\n## Highlights\n\n## Week 4 (09/21 to 09/27)\n\n"
            "### Tuesday\n\n#### Completed work\n\n   \n- Completed task\n\n"
            "#### Empty category one\n\n#### Empty category two\n",
            encoding="utf-8",
        )
        self.run_journal("close-day", "--date", "2026-09-22")

        updated = self.month("September-2026.md")
        self.assertIn("#### Completed work\n- Completed task", updated)
        self.assertNotIn("#### Empty category one", updated)
        self.assertNotIn("#### Empty category two", updated)

    def test_rollover_carries_open_tasks_and_finalizes_month(self) -> None:
        self.run_journal("add", "--date", "2026-09-29", "--state", "completed", "--text", "Closed support tickets")
        self.run_journal("add", "--date", "2026-09-30", "--state", "open", "--heading", "Recruiter / application block", "--text", "Follow up with client", "--reference-date", "2026-09-30")
        rollover = self.run_journal("rollover", "--date", "2026-10-02")

        result = json.loads(rollover.stdout)
        self.assertEqual(result["unfinalized_months"], ["September-2026.md"])
        self.assertEqual(result["carried_tasks"], ["Follow up with client"])
        self.assertNotIn("[ ] Follow up with client", self.month("September-2026.md"))
        self.assertIn("#### Recruiter / application block\n- [ ] Follow up with client", self.month("October-2026.md"))

        self.run_journal("finalize", "--month", "September-2026.md", "--highlight", "Resolved outstanding support work")
        september = self.month("September-2026.md")
        self.assertIn("- Resolved outstanding support work", september)
        self.assertNotIn("<!--", september)
        self.assertIn("- Closed support tickets", september)

        repeated = json.loads(self.run_journal("rollover", "--date", "2026-10-03").stdout)
        self.assertEqual(repeated, {"unfinalized_months": [], "carried_tasks": []})
        self.assertEqual(self.month("September-2026.md"), september)
        with self.assertRaises(subprocess.CalledProcessError):
            self.run_journal("finalize", "--month", "September-2026.md", "--highlight", "Replacement summary")
        self.assertEqual(self.month("September-2026.md"), september)

    def test_rollover_recognizes_existing_highlights_without_marker(self) -> None:
        journal = self.journals / "September-2026.md"
        content = "# September 2026\n\n## Highlights\n\n- Shipped the release\n"
        journal.write_text(content, encoding="utf-8")

        result = json.loads(self.run_journal("rollover", "--date", "2026-10-01").stdout)
        self.assertEqual(result, {"unfinalized_months": [], "carried_tasks": []})
        self.assertEqual(journal.read_text(encoding="utf-8"), content)

    def test_finalize_rejects_empty_highlights_without_changing_journal(self) -> None:
        self.run_journal("ensure-month", "--date", "2026-09-30")
        original = self.month("September-2026.md")
        for highlights in ((), ("--highlight", "   ")):
            with self.assertRaises(subprocess.CalledProcessError):
                self.run_journal("finalize", "--month", "September-2026.md", *highlights)
            self.assertEqual(self.month("September-2026.md"), original)


if __name__ == "__main__":
    unittest.main()
