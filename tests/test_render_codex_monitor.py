import importlib.util
from importlib.machinery import SourceFileLoader
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "bin" / "axiom-render-codex-monitor"
LOADER = SourceFileLoader("axiom_render_codex_monitor", str(SCRIPT))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RenderCodexMonitorTest(unittest.TestCase):
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
