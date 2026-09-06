import importlib.util
import json
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "bin" / "piston-todo"
LOADER = SourceFileLoader("axiom_todo", str(SCRIPT))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TodoTest(unittest.TestCase):
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
