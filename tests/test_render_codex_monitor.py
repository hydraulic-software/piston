import importlib.util
from importlib.machinery import SourceFileLoader
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "bin" / "axiom-render-codex-monitor"
LOADER = SourceFileLoader("axiom_render_codex_monitor", str(SCRIPT))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RenderCodexMonitorTest(unittest.TestCase):
    def test_load_todos_normalizes_progress(self):
        with tempfile.TemporaryDirectory() as directory:
            original = MODULE.TODO_FILE
            MODULE.TODO_FILE = Path(directory) / "todo.json"
            MODULE.TODO_FILE.write_text(json.dumps({"items": [{
                "id": "archive",
                "text": "Index archive",
                "status": "started",
                "progress": {"current": 18, "total": 390, "label": "18 of 390 articles"},
            }]}))
            try:
                todos = MODULE.load_todos("2026-08-17")
            finally:
                MODULE.TODO_FILE = original

        self.assertEqual(
            {"current": 18, "total": 390, "percent": 4.6, "label": "18 of 390 articles"},
            todos[0]["progress"],
        )

    def test_recent_rollout_starts_at_preceding_user_turn(self):
        old_user = {"timestamp": "2026-07-15T21:00:00Z", "payload": {"type": "user_message"}}
        old_output = {"timestamp": "2026-07-15T21:01:00Z", "payload": {"type": "agent_message"}}
        current_output = {"timestamp": "2026-07-15T22:01:00Z", "payload": {"type": "agent_message"}}

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rollout.jsonl"
            path.write_text("\n".join(map(json.dumps, (old_user, old_output, current_output))) + "\n")
            since = dt.datetime(2026, 7, 15, 22, 0, tzinfo=dt.timezone.utc)

            raw_lines, wakeup_index_offset = MODULE.recent_rollout_lines(path, since)
            lines = [json.loads(line) for line in raw_lines]

        self.assertEqual([old_user, old_output, current_output], lines)
        self.assertEqual(0, wakeup_index_offset)

    def test_recent_rollout_discards_crossing_turn_after_new_user(self):
        old_user = {"timestamp": "2026-07-15T21:00:00Z", "payload": {"type": "user_message"}}
        crossing_output = {"timestamp": "2026-07-15T22:01:00Z", "payload": {"type": "agent_message"}}
        current_user = {"timestamp": "2026-07-15T22:02:00Z", "payload": {"type": "user_message"}}
        current_output = {"timestamp": "2026-07-15T22:03:00Z", "payload": {"type": "agent_message"}}

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rollout.jsonl"
            path.write_text("\n".join(map(json.dumps, (old_user, crossing_output, current_user, current_output))) + "\n")
            since = dt.datetime(2026, 7, 15, 22, 0, tzinfo=dt.timezone.utc)

            raw_lines, wakeup_index_offset = MODULE.recent_rollout_lines(path, since)
            lines = [json.loads(line) for line in raw_lines]

        self.assertEqual([current_user, current_output], lines)
        self.assertEqual(1, wakeup_index_offset)

    def test_typed_tool_output_is_flattened(self):
        output = [
            {"type": "input_text", "text": "Script completed\nOutput:\n"},
            {"type": "input_text", "text": "hello\n"},
        ]

        self.assertEqual("Script completed\nOutput:\nhello\n", MODULE.content_text(output))

    def test_standard_mail_prompt_has_generic_label(self):
        prompt = (
            "The time is Tue Jul 14 03:08:35 PM CEST 2026. You've got mail! "
            "Find it in your ~/Maildir, handle the message end-to-end if practical, "
            "and update any upstream ticket."
        )

        self.assertEqual("Mail check", MODULE.clean_prompt(prompt))

    def test_exec_command_is_extracted_from_javascript_wrapper(self):
        body = (
            'const r = await tools.exec_command({cmd:"git status --short && printf \'\\nDone\\n\'",'
            'workdir:"/home/axiom"}); text(r.output);'
        )

        self.assertEqual(
            ["git status --short && printf '\nDone\n'"],
            MODULE.tool_commands("exec", body),
        )
        self.assertEqual(
            "git status --short && printf '\nDone\n'",
            MODULE.tool_detail("exec", body),
        )

    def test_multiple_exec_commands_are_listed(self):
        body = (
            'const a = tools.exec_command({cmd:"first"}); '
            'const b = tools.exec_command({cmd:"second"});'
        )

        self.assertEqual(["first", "second"], MODULE.tool_commands("exec", body))
        self.assertEqual("first (+1 more)", MODULE.tool_summary("exec", body))


if __name__ == "__main__":
    unittest.main()
