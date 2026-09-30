import runpy
import tempfile
import unittest
from pathlib import Path

MODULE = runpy.run_path(str(Path(__file__).parents[1] / "bin/piston-update-agent-instructions"))


class AgentInstructionsTest(unittest.TestCase):
    def test_preserves_policy_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "AGENTS.md"
            path.write_text("# Employee\nNever disclose secrets.\n")
            MODULE["update"](path)
            first = path.read_text()
            MODULE["update"](path)
            self.assertEqual(first, path.read_text())
            self.assertTrue(first.startswith("# Employee\nNever disclose secrets."))
            self.assertIn("piston-todo schedule", first)

    def test_bad_markers_fail_without_change(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "AGENTS.md"
            text = "Policy\n<!-- piston-managed:start -->"
            path.write_text(text)
            with self.assertRaises(SystemExit):
                MODULE["update"](path)
            self.assertEqual(text, path.read_text())
