import importlib.util
import json
import tempfile
import unittest
from datetime import date
from importlib.machinery import SourceFileLoader
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "bin" / "piston-todo"
LOADER = SourceFileLoader("axiom_todo", str(SCRIPT))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TodoTest(unittest.TestCase):
    def test_month_end_preserves_anchor(self):
        self.assertEqual(date(2024, 2, 29), MODULE.advance_month(date(2024, 1, 31), 31))
        self.assertEqual(date(2024, 3, 31), MODULE.advance_month(date(2024, 2, 29), 31))
        self.assertEqual(date(2025, 1, 31), MODULE.advance_month(date(2024, 12, 31), 31))

    def test_recurring_task_materializes_once_and_completion_advances(self):
        with tempfile.TemporaryDirectory() as directory:
            original = MODULE.TODO_FILE
            MODULE.TODO_FILE = Path(directory) / "todo.json"
            try:
                MODULE.main(["schedule", "triage", "Review; done when recorded", "--next-due", "2020-01-31"])
                MODULE.main(["tick"])
                MODULE.main(["tick"])
                data = json.loads(MODULE.TODO_FILE.read_text())
                self.assertEqual(1, len(data["items"]))
                item_id = data["items"][0]["id"]
                MODULE.main(["start", item_id])
                MODULE.main(["tick"])
                self.assertEqual(1, len(json.loads(MODULE.TODO_FILE.read_text())["items"]))
                MODULE.main(["done", item_id])
                MODULE.main(["done", item_id])
                MODULE.main(["tick"])
                data = json.loads(MODULE.TODO_FILE.read_text())
                self.assertEqual(1, len(data["items"]))
                self.assertGreater(date.fromisoformat(data["schedules"][0]["next_due"]), date.today())
                self.assertNotIn("occurrence_id", data["schedules"][0])
                MODULE.main(["add", "Unrelated task", "--id", "other"])
                self.assertEqual(1, len(json.loads(MODULE.TODO_FILE.read_text())["schedules"]))
            finally:
                MODULE.TODO_FILE = original

    def test_future_schedule_and_duplicate_id(self):
        with tempfile.TemporaryDirectory() as directory:
            original = MODULE.TODO_FILE
            MODULE.TODO_FILE = Path(directory) / "todo.json"
            try:
                args = ["schedule", "future", "Future task", "--next-due", "2099-01-01"]
                MODULE.main(args)
                MODULE.main(["tick"])
                self.assertEqual([], json.loads(MODULE.TODO_FILE.read_text())["items"])
                with self.assertRaisesRegex(SystemExit, "schedule already exists"):
                    MODULE.main(args)
            finally:
                MODULE.TODO_FILE = original

    def test_progress_command_persists_structured_progress(self):
        with tempfile.TemporaryDirectory() as directory:
            original = MODULE.TODO_FILE
            MODULE.TODO_FILE = Path(directory) / "todo.json"
            try:
                MODULE.main(["add", "Long project", "--id", "long-project"])
                MODULE.main(["progress", "long-project", "18", "390", "--label", "18 of 390 articles"])
                item = json.loads(MODULE.TODO_FILE.read_text())["items"][0]
            finally:
                MODULE.TODO_FILE = original

        self.assertEqual(
            {"current": 18, "total": 390, "label": "18 of 390 articles"},
            item["progress"],
        )

    def test_progress_rejects_current_above_total(self):
        with self.assertRaisesRegex(SystemExit, "invalid progress"):
            MODULE.main(["progress", "missing", "11", "10"])


if __name__ == "__main__":
    unittest.main()
