import importlib.machinery
import importlib.util
import os
from pathlib import Path
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
        os.environ["BOT_AUTH_RESULTS_ID"] = "hq.example"
        self.filter = load_filter()

    def tearDown(self):
        if self.old_authserv_id is None:
            os.environ.pop("BOT_AUTH_RESULTS_ID", None)
        else:
            os.environ["BOT_AUTH_RESULTS_ID"] = self.old_authserv_id

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


if __name__ == "__main__":
    unittest.main()
