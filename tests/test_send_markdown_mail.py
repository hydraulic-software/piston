import argparse
import email
import email.policy
import importlib.machinery
import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "bin" / "piston-send-markdown-mail"


def load_script():
    loader = importlib.machinery.SourceFileLoader("send_markdown_mail", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class ReplyParentGuardTest(unittest.TestCase):
    def test_reply_all_preserves_participants_and_excludes_self(self):
        with tempfile.TemporaryDirectory() as directory:
            mail = Path(directory) / "message"
            mail.write_text('From: Daneel <daneel@example.com>\nTo: Mike <mike@example.com>, assistant@example.com\nCc: Daneel <daneel@example.com>, Other <other@example.com>\nSubject: Test\nMessage-ID: <x>\n\nBody')
            args = self.args(mail, '<x>')
            args.reply_all = True
            self.module.render_with_pandoc = lambda text, _: text
            message = self.module.build_message(args, 'Reply')
            self.assertEqual(str(message['To']), 'Daneel <daneel@example.com>, Mike <mike@example.com>')
            self.assertEqual(str(message['Cc']), 'Other <other@example.com>')

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
            signature=None,
            in_reply_to=None,
            references=None,
            attach=[],
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

    def test_signature_is_plain_and_subtle_html(self):
        args = self.args(None, "")
        args.to = "person@example.com"
        args.subject = "Test"
        args.signature = "R. Axiom, AI employee."
        self.module.render_with_pandoc = lambda text, output_format: (
            "<p>Body</p>" if output_format == "html5" else "Body"
        )

        message = self.module.build_message(args, "Body")
        plain = message.get_body(preferencelist=("plain",)).get_content()
        rich = message.get_body(preferencelist=("html",)).get_content()
        self.assertIn("Body\n\n---\nR. Axiom, AI employee.", plain)
        self.assertIn("color:#777", rich)
        self.assertIn("R. Axiom, AI employee.", rich)


class AttachmentTest(unittest.TestCase):
    def setUp(self):
        self.module = load_script()
        self.module.render_with_pandoc = lambda text, output_format: (
            f"<p>{text}</p>" if output_format == "html5" else text
        )

    def args(self, attachments):
        return argparse.Namespace(
            to="person@example.com",
            subject="Attached form",
            reply_mail=None,
            expect_reply_message_id=None,
            from_header="Assistant <assistant@example.com>",
            envelope_from="assistant@example.com",
            reply_to=None,
            signature=None,
            in_reply_to=None,
            references=None,
            attach=attachments,
        )

    def test_named_attachment_preserves_both_body_alternatives(self):
        with tempfile.TemporaryDirectory() as directory:
            attachment = Path(directory) / "signed form.pdf"
            attachment.write_bytes(b"%PDF-test")

            message = self.module.build_message(self.args([attachment]), "Please sign this form.")
            reparsed = email.message_from_bytes(message.as_bytes(), policy=email.policy.default)

            self.assertEqual(reparsed.get_body(preferencelist=("plain",)).get_content().strip(), "Please sign this form.")
            self.assertEqual(reparsed.get_body(preferencelist=("html",)).get_content().strip(), "<p>Please sign this form.</p>")
            parts = list(reparsed.iter_attachments())
            self.assertEqual(len(parts), 1)
            self.assertEqual(parts[0].get_filename(), "signed form.pdf")
            self.assertEqual(parts[0].get_content_type(), "application/pdf")
            self.assertEqual(parts[0].get_payload(decode=True), b"%PDF-test")

    def test_missing_attachment_is_rejected_before_send(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.pdf"
            with self.assertRaisesRegex(SystemExit, "Attachment is not a regular file"):
                self.module.build_message(self.args([missing]), "Body")


if __name__ == "__main__":
    unittest.main()
