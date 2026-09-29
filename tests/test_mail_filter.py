import importlib.machinery
import importlib.util
import os
from pathlib import Path
import pwd
import unittest


FILTER_PATH = Path(__file__).parents[1] / "bin" / "piston-mail-filter"


def load_filter():
    loader = importlib.machinery.SourceFileLoader("axiom_mail_filter", str(FILTER_PATH))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class MailAuthenticationTest(unittest.TestCase):
    def setUp(self):
        self.old_authserv_id = os.environ.get("BOT_AUTH_RESULTS_ID")
        self.old_trust_local = os.environ.get("BOT_TRUST_LOCAL_SUBMISSION")
        self.old_local_domain = os.environ.get("BOT_LOCAL_MAIL_DOMAIN")
        os.environ["BOT_AUTH_RESULTS_ID"] = "hq.example"
        os.environ["BOT_TRUST_LOCAL_SUBMISSION"] = "1"
        os.environ["BOT_LOCAL_MAIL_DOMAIN"] = "hq.example"
        self.filter = load_filter()

    def tearDown(self):
        if self.old_authserv_id is None:
            os.environ.pop("BOT_AUTH_RESULTS_ID", None)
        else:
            os.environ["BOT_AUTH_RESULTS_ID"] = self.old_authserv_id
        if self.old_trust_local is None:
            os.environ.pop("BOT_TRUST_LOCAL_SUBMISSION", None)
        else:
            os.environ["BOT_TRUST_LOCAL_SUBMISSION"] = self.old_trust_local
        if self.old_local_domain is None:
            os.environ.pop("BOT_LOCAL_MAIL_DOMAIN", None)
        else:
            os.environ["BOT_LOCAL_MAIL_DOMAIN"] = self.old_local_domain

    @staticmethod
    def message(authentication_results="", from_address="sender@example.com", forged=False):
        trusted = f"Authentication-Results: {authentication_results}\n" if authentication_results else ""
        forged_header = (
            "Authentication-Results: hq.example; dkim=pass header.d=example.com\n" if forged else ""
        )
        return (
            f"{trusted}"
            "Received: from mail.example.net by hq.example with ESMTPS\n"
            f"{forged_header}"
            f"From: Sender <{from_address}>\n"
            "To: bot@hq.example\n"
            "Subject: Test\n"
            "\n"
            "Hello\n"
        ).encode()

    def test_accepts_trusted_aligned_dkim_pass(self):
        allowed, reason = self.filter.dkim_authenticated(
            self.message("hq.example; dkim=pass header.d=example.com header.s=mail")
        )
        self.assertTrue(allowed)
        self.assertEqual("aligned-dkim-pass", reason)

    def test_rejects_unsigned_mail(self):
        self.assertEqual(
            (False, "missing-aligned-dkim-pass"),
            self.filter.dkim_authenticated(self.message()),
        )

    def test_rejects_unaligned_signing_domain(self):
        self.assertEqual(
            (False, "missing-aligned-dkim-pass"),
            self.filter.dkim_authenticated(
                self.message("hq.example; dkim=pass header.d=attacker.example")
            ),
        )

    def test_rejects_forged_authentication_results_below_local_received(self):
        self.assertEqual(
            (False, "missing-aligned-dkim-pass"),
            self.filter.dkim_authenticated(self.message(forged=True)),
        )

    def test_rejects_untrusted_authserv_id(self):
        self.assertEqual(
            (False, "missing-aligned-dkim-pass"),
            self.filter.dkim_authenticated(
                self.message("attacker.example; dkim=pass header.d=example.com")
            ),
        )

    @staticmethod
    def local_message(from_address, received=None):
        username = pwd.getpwuid(os.getuid()).pw_name
        top_received = received or f"by hq.example (Postfix, from userid {os.getuid()}) id 12345"
        return (
            f"Received: {top_received}\n"
            f"From: {username.title()} <{from_address}>\n"
            "To: bot@hq.example\n"
            "Subject: Local test\n\nHello\n"
        ).encode()

    def test_accepts_matching_authenticated_local_submission(self):
        username = pwd.getpwuid(os.getuid()).pw_name
        self.assertEqual(
            (True, "authenticated-local-submission"),
            self.filter.local_submission_authenticated(
                self.local_message(f"{username}@hq.example")
            ),
        )

    def test_rejects_local_submission_with_mismatched_sender(self):
        self.assertEqual(
            (False, "local-submission-sender-mismatch"),
            self.filter.local_submission_authenticated(
                self.local_message("someone-else@hq.example")
            ),
        )

    def test_rejects_forged_local_received_below_smtp_hop(self):
        username = pwd.getpwuid(os.getuid()).pw_name
        message = (
            "Received: from attacker.example by hq.example with ESMTPS\n"
            f"Received: by hq.example (Postfix, from userid {os.getuid()}) id forged\n"
            f"From: {username.title()} <{username}@hq.example>\n"
            "To: bot@hq.example\nSubject: Forged\n\nHello\n"
        ).encode()
        self.assertEqual(
            (False, "missing-local-postfix-uid"),
            self.filter.local_submission_authenticated(message),
        )


if __name__ == "__main__":
    unittest.main()
