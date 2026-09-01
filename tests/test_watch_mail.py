import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "bin" / "axiom-watch-mail"


class WatchMailTest(unittest.TestCase):
    def test_events_during_run_are_queued_and_duplicate_events_are_harmless(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            bin_dir = home / ".local" / "bin"
            maildir = home / "Maildir" / "new"
            bin_dir.mkdir(parents=True)
            maildir.mkdir(parents=True)
            (maildir / "first").touch()

            runner = bin_dir / "axiom-codex-runner"
            runner.write_text(
                "#!/bin/sh\n"
                f'printf "%s\\n" "$*" >> {home / "runs"}\n'
                f'if [ -f {maildir / "first"} ]; then rm {maildir / "first"}; touch {maildir / "second"}; '
                f'else rm -f {maildir / "second"}; fi\n'
            )
            runner.chmod(0o755)

            inotifywait = bin_dir / "inotifywait"
            inotifywait.write_text("#!/bin/sh\nprintf 'watch ready\\nsecond arrived\\nduplicate\\n'\n")
            inotifywait.chmod(0o755)

            env = os.environ.copy()
            env["HOME"] = str(home)
            subprocess.run([str(SCRIPT)], env=env, check=True, timeout=5)

            self.assertEqual(["mail", "mail"], (home / "runs").read_text().splitlines())
            self.assertEqual([], list(maildir.iterdir()))


if __name__ == "__main__":
    unittest.main()
