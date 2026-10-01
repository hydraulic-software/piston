import importlib.util
from importlib.machinery import SourceFileLoader
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "bin" / "piston-render-codex-monitor"
LOADER = SourceFileLoader("axiom_render_codex_monitor", str(SCRIPT))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RenderCodexMonitorTest(unittest.TestCase):
    def test_command_cards_have_scoped_spacing_and_dividers(self):
        shell = MODULE.day_shell("2026-10-01")
        self.assertIn('<section class="tool-result">', shell)
        self.assertIn('.tool-result + .tool-result {', shell)
        self.assertIn('border-top: 1px solid var(--tool-line)', shell)

    def test_shell_envelope_is_readable_and_plain_json_is_preserved(self):
        raw = json.dumps({"output": "hello\n", "exit_code": 2, "wall_time_seconds": 0.5})
        result = MODULE.readable_tool_output(raw)
        self.assertEqual("hello\n", result["text"])
        self.assertEqual("exit 2 · 0.5s", result["status"])
        self.assertIn('"ticket": 42', MODULE.readable_tool_output('{"ticket":42}')["text"])
        self.assertIn('"output": "user data"', MODULE.readable_tool_output('{"output":"user data"}')["text"])
        prefixed = MODULE.readable_tool_output('Script completed\n{"chunk_id":"abc","output":"decoded","exit_code":0}')
        self.assertEqual("Script completed\n\ndecoded", prefixed["text"])

    def test_multiple_results_and_partial_text(self):
        raw = '{"output":"first","exit_code":0}{"output":"second","session_id":12} tail'
        result = MODULE.readable_tool_output(raw)
        self.assertEqual("first\n\nsecond\n\ntail", result["text"])
        self.assertIn("running session 12", result["status"])
        self.assertEqual("<script>plain</script>", MODULE.readable_tool_output("<script>plain</script>")["text"])

    def test_future_schedules_and_active_occurrence_are_exposed(self):
        with tempfile.TemporaryDirectory() as directory:
            old = MODULE.TODO_FILE
            MODULE.TODO_FILE = Path(directory) / "todo.json"
            try:
                MODULE.TODO_FILE.write_text(json.dumps({"schedules": [{"id": "monthly", "text": "<review>",
                    "cadence": "monthly", "next_due": "2099-01-31"}], "items": [
                    {"id": "occurrence", "schedule_id": "monthly", "status": "started"}]}))
                schedule = MODULE.load_schedules()[0]
                self.assertEqual("2099-01-31", schedule["next_due"])
                self.assertEqual({"id": "occurrence", "status": "started"}, schedule["occurrence"])
                shell = MODULE.day_shell("2026-09-30")
                self.assertIn("Scheduled tasks", shell)
                self.assertIn("escapeHtml(s.text)", shell)
            finally:
                MODULE.TODO_FILE = old

    @staticmethod
    def thread(path):
        return {
            "id": "thread-1",
            "rollout_path": str(path),
            "title": "Synthetic thread",
            "cwd": str(Path.home()),
            "model": "test-model",
        }

    def test_recent_index_update_replaces_today_without_dropping_history(self):
        yesterday = {"day": "2026-08-31", "wakeups": [1], "segments": []}
        today = {"day": "2026-09-01", "wakeups": [1], "segments": []}
        refreshed_today = {
            "day": "2026-09-01",
            "wakeups": [1, 2],
            "segments": [{"left": 10.0, "width": 1.0, "kind": "mail", "shade": 0}],
        }

        with tempfile.TemporaryDirectory() as directory:
            old_output_dir = MODULE.OUTPUT_DIR
            MODULE.OUTPUT_DIR = Path(directory)
            try:
                MODULE.write_index_data([today, yesterday])
                self.assertTrue(MODULE.update_index_data([refreshed_today]))
                payload = json.loads((Path(directory) / "index.json").read_text())
            finally:
                MODULE.OUTPUT_DIR = old_output_dir

        self.assertEqual(["2026-09-01", "2026-08-31"], [day["day"] for day in payload["days"]])
        self.assertEqual(2, payload["days"][0]["wakeup_count"])
        self.assertEqual(1, len(payload["days"][0]["segments"]))

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

    def test_mixed_rollout_schemas_deduplicate_and_recent_matches_full(self):
        def record(timestamp, event_type, payload):
            return {"timestamp": timestamp, "type": event_type, "payload": payload}

        records = [
            # Codex-injected setup context is a user-role message in the new
            # schema, but it is not an actual wakeup boundary.
            record(
                "2026-07-15T21:58:00Z",
                "response_item",
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "<recommended_plugins>setup</recommended_plugins>"}],
                },
            ),
            record("2026-07-15T21:59:00Z", "event_msg", {"type": "user_message", "message": "Old turn"}),
            record(
                "2026-07-15T22:00:30Z",
                "response_item",
                {
                    "type": "message",
                    "role": "assistant",
                    "phase": "commentary",
                    "content": [{"type": "output_text", "text": "Crossing midnight"}],
                },
            ),
            record(
                "2026-07-15T22:01:00Z",
                "response_item",
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "New turn"}],
                },
            ),
            # Some Codex versions emit both representations. These adjacent
            # compatibility records must not create duplicate wakeups/prose.
            record("2026-07-15T22:01:00Z", "event_msg", {"type": "user_message", "message": "New turn"}),
            record(
                "2026-07-15T22:01:10Z",
                "response_item",
                {
                    "type": "message",
                    "role": "assistant",
                    "phase": "commentary",
                    "content": [{"type": "output_text", "text": "Working"}],
                },
            ),
            record(
                "2026-07-15T22:01:10Z",
                "event_msg",
                {"type": "agent_message", "phase": "commentary", "message": "Working"},
            ),
            record(
                "2026-07-15T22:01:20Z",
                "response_item",
                {"type": "function_call", "name": "exec_command", "arguments": '{"cmd":"true"}', "call_id": "1"},
            ),
            record(
                "2026-07-15T22:01:21Z",
                "response_item",
                {"type": "function_call_output", "output": "ok", "call_id": "1"},
            ),
            record(
                "2026-07-15T22:02:00Z",
                "response_item",
                {
                    "type": "message",
                    "role": "assistant",
                    "phase": "final_answer",
                    "content": [{"type": "output_text", "text": "Finished"}],
                },
            ),
        ]

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rollout.jsonl"
            path.write_text("\n".join(map(json.dumps, records)) + "\n")
            thread = self.thread(path)
            full = MODULE.parse_rollout(thread)
            recent = MODULE.parse_rollout(
                thread,
                dt.datetime(2026, 7, 15, 22, 0, tzinfo=dt.timezone.utc),
            )

        self.assertEqual(["New turn", "Old turn"], [item["prompt"] for item in full])
        self.assertEqual(["New turn"], [item["prompt"] for item in recent])
        current = full[0]
        self.assertEqual(1, sum(entry.get("plain") == "Working" for entry in current["entries"]))
        self.assertEqual(["commentary", "tool", "final"], [entry["role"] for entry in current["entries"]])
        self.assertEqual(
            [(entry["kind"], entry.get("role"), entry.get("plain")) for entry in current["entries"]],
            [(entry["kind"], entry.get("role"), entry.get("plain")) for entry in recent[0]["entries"]],
        )

    def test_monitor_defaults_are_neutral_piston_paths(self):
        self.assertEqual("Piston Monitor", MODULE.MONITOR_NAME)
        self.assertEqual(Path.home() / ".local/state/piston/todo.json", MODULE.TODO_FILE)
        self.assertEqual(Path.home() / ".local/state/piston/runs", MODULE.RUN_LOG_DIR)
        self.assertIn("Piston Monitor", MODULE.day_shell("2026-09-29"))

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
