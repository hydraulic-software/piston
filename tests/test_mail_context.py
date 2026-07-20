import importlib.machinery
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "bin" / "axiom-mail-context"


def load_script():
    loader = importlib.machinery.SourceFileLoader("mail_context", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class MailContextTest(unittest.TestCase):
    def setUp(self):
        self.module = load_script()

    def test_lists_exact_paths_and_message_ids_newest_first(self):
        with tempfile.TemporaryDirectory() as directory:
            maildir = Path(directory)
            older = maildir / "older-message"
            newer = maildir / "newer-message"
            older.write_text(
                "From: Old Sender <old@example.com>\nMessage-ID: <old@example.com>\nSubject: Old\n\nBody\n",
                encoding="utf-8",
            )
            newer.write_text(
                "From: New Sender <new@example.com>\nMessage-ID: <new@example.com>\nSubject: New\n\nBody\n",
                encoding="utf-8",
            )
            os.utime(older, ns=(1_000_000_000, 1_000_000_000))
            os.utime(newer, ns=(2_000_000_000, 2_000_000_000))

            output = self.module.render_mail_context(maildir)

            self.assertIn(f"Source: {newer}", output)
            self.assertIn("Message-ID: <new@example.com>", output)
            self.assertLess(output.index(str(newer)), output.index(str(older)))

    def test_reports_an_empty_maildir(self):
        with tempfile.TemporaryDirectory() as directory:
            output = self.module.render_mail_context(Path(directory))
            self.assertIn("No message files were present", output)


if __name__ == "__main__":
    unittest.main()
