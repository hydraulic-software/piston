import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("setup_shared_mail", Path(__file__).parents[1] / "scripts/setup-shared-mail.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SetupSharedMailTest(unittest.TestCase):
    def test_preserves_auth_and_is_rerunnable(self):
        old = '"|env BOT_REQUIRE_ALIGNED_DKIM=1 BOT_AUTH_RESULTS_ID=hq.example BOT_TRUST_LOCAL_SUBMISSION=1 /home/bot/.local/bin/piston-mail-filter"'
        rendered = module.forward_content(old, "/var/lib/test/contacts", ["owner@example.com"])
        self.assertIn("BOT_REQUIRE_ALIGNED_DKIM=1", rendered)
        self.assertIn("BOT_TRUST_LOCAL_SUBMISSION=1", rendered)
        self.assertEqual(rendered, module.forward_content(rendered, "/var/lib/test/contacts", ["owner@example.com"]))

    def test_refuses_unmanaged_or_unauthenticated_forward(self):
        for text in ['"person@example.com"', '"|env /home/bot/.local/bin/piston-mail-filter"', '"|env A=x /bin/evil"']:
            with self.assertRaises(ValueError):
                module.forward_content(text, "/var/lib/test/contacts", ["owner@example.com"])
