import argparse
import importlib.machinery
import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "bin" / "axiom-send-markdown-mail"


def load_script():
    loader = importlib.machinery.SourceFileLoader("send_markdown_mail", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class ReplyParentGuardTest(unittest.TestCase):
    def setUp(self):
        self.module = load_script()

    def args(self, reply_mail: Path, expected: str):
        return argparse.Namespace(
            to=None,
            subject=None,
            reply_mail=reply_mail,
            expect_reply_message_id=expected,
            from_header="Assistant <assistant@example.com>",
            envelope_from="assistant@example.com",
            reply_to=None,
            in_reply_to=None,
            references=None,
        )

    def test_expected_message_id_accepts_the_intended_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            mail = Path(directory) / "message"
            mail.write_text(
                "From: person@example.com\nSubject: Test\nMessage-ID: <expected@example.com>\n\nBody\n",
                encoding="utf-8",
            )
            self.module.render_with_pandoc = lambda text, _format: text
            message = self.module.build_message(self.args(mail, "<expected@example.com>"), "Reply")
            self.assertEqual(message["In-Reply-To"], "<expected@example.com>")

    def test_expected_message_id_rejects_a_different_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            mail = Path(directory) / "message"
            mail.write_text(
                "From: person@example.com\nSubject: Test\nMessage-ID: <newer@example.com>\n\nBody\n",
                encoding="utf-8",
            )
            self.module.render_with_pandoc = lambda text, _format: text
            with self.assertRaisesRegex(SystemExit, "Reply message mismatch"):
                self.module.build_message(self.args(mail, "<expected@example.com>"), "Reply")


if __name__ == "__main__":
    unittest.main()
