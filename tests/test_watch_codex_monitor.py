import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "bin" / "axiom-watch-codex-monitor"


class WatchCodexMonitorTest(unittest.TestCase):
    def test_frequent_events_are_throttled(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            bin_dir = home / ".local" / "bin"
            state_dir = home / ".local" / "state" / "axiom"
            sessions_dir = home / ".codex" / "sessions"
            bin_dir.mkdir(parents=True)
            state_dir.mkdir(parents=True)
            sessions_dir.mkdir(parents=True)
            (home / ".codex" / "state_5.sqlite").touch()
            (home / ".codex" / "state_5.sqlite-wal").touch()
            (state_dir / "todo.json").touch()
            (state_dir / "runs").mkdir()
            output_dir = home / "private_html"
            output_dir.mkdir()
            today = subprocess.check_output(["date", "+%F"], text=True).strip()
            (output_dir / "index.html").write_text(f'href="{today}.html"')

            render_log = home / "renders"
            renderer = bin_dir / "axiom-render-codex-monitor"
            renderer.write_text(f'#!/bin/sh\nprintf "%s %s\\n" "$(date +%s.%N)" "$*" >> {render_log}\n')
            renderer.chmod(0o755)

            # Keep stdout open long enough for the watcher to hit its one-second
            # test interval after receiving several immediate events.
            inotifywait = bin_dir / "inotifywait"
            inotifywait.write_text(
                f"#!/bin/sh\nprintf '%s' \"$*\" > {home / 'inotify-arguments'}\n"
                "printf 'one\\ntwo\\nthree\\n'\nsleep 2\n"
            )
            inotifywait.chmod(0o755)

            env = os.environ.copy()
            env.update({"HOME": str(home), "BOT_MONITOR_MIN_INTERVAL_SECONDS": "1"})
            subprocess.run([str(SCRIPT)], env=env, check=True, timeout=5)

            renders = [value.split(maxsplit=1) for value in render_log.read_text().splitlines()]
            timestamps = [float(value[0]) for value in renders]
            self.assertEqual(2, len(timestamps))
            self.assertGreaterEqual(timestamps[1] - timestamps[0], 0.9)
            self.assertEqual(["--recent"], renders[1][1:])

            # Database housekeeping has no user-visible monitor content and
            # must not be part of the inotify watch set.
            invocation = (home / "inotify-arguments").read_text()
            self.assertNotIn("state_5.sqlite", invocation)
            self.assertIn("modify,close_write,create,move,delete", invocation)

if __name__ == "__main__":
    unittest.main()
