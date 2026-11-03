import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location("setup_shared_mail", Path(__file__).parents[1] / "scripts/setup-shared-mail.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SetupSharedMailTest(unittest.TestCase):
    def test_delivery_acl_check_has_no_supplementary_groups(self):
        with patch.object(module.subprocess, "run") as run:
            module.grant_delivery_access(SimpleNamespace(pw_uid=1234, pw_gid=2345), Path('/state'), Path('/state/contacts'))
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(commands[0], ['setfacl', '-m', 'u:1234:rx', '/state'])
        self.assertEqual(commands[1], ['setfacl', '-m', 'u:1234:rw', '/state/contacts'])
        self.assertIn('--clear-groups', commands[2])
        self.assertIn('--reuid=1234', commands[2])
        self.assertTrue(all(call.kwargs['check'] for call in run.call_args_list))

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
