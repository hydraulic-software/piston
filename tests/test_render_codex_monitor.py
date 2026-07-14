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


if __name__ == "__main__":
    unittest.main()
