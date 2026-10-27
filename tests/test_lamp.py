"""Exercise the CLI against an isolated real tmux server."""
import os
import re
from pathlib import Path
import subprocess
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
LAMP = ROOT / "bin" / "lamp"


class LampTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = "lamp-test-" + uuid.uuid4().hex[:12]
        cls.tmux = ["tmux", "-L", cls.server]
        subprocess.run(cls.tmux + ["-f", "/dev/null", "new-session", "-d", "-s", "test"], check=True)
        cls.pane = subprocess.check_output(cls.tmux + ["display-message", "-p", "#{pane_id}"], text=True).strip()
        cls.socket = subprocess.check_output(cls.tmux + ["display-message", "-p", "#{socket_path},#{pid},0"], text=True).strip()
        cls.env = dict(os.environ, TMUX=cls.socket, TMUX_PANE=cls.pane)

    @classmethod
    def tearDownClass(cls):
        subprocess.run(cls.tmux + ["kill-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def lamp(self, *args, env=None, check=True):
        return subprocess.run([str(LAMP), *args], env=env or self.env, text=True, capture_output=True, check=check)

    def test_isolated_panel_state_and_dynamic_names(self):
        other = subprocess.check_output(self.tmux + ["split-window", "-d", "-P", "-F", "#{pane_id}"], text=True).strip()
        self.addCleanup(lambda: subprocess.run(self.tmux + ["kill-pane", "-t", other], check=False))
        self.lamp("set", "working", "--name", "phone use", "--detail", "检查微信")
        self.lamp("set", "waiting", "--name", "review", "--pane", other)
        self.assertEqual(self.lamp("get", "--field", "state").stdout.strip(), "working")
        self.assertEqual(self.lamp("get", "--field", "state", "--pane", other).stdout.strip(), "waiting")
        self.assertEqual(self.lamp("get", "--field", "name").stdout.strip(), "phone use")
        self.lamp("set", "working", "--name", "dev")
        self.assertEqual(self.lamp("get", "--field", "name").stdout.strip(), "dev")
        self.assertEqual(self.lamp("get", "--field", "detail").stdout.strip(), "")

    def test_unknown_and_validation(self):
        other = subprocess.check_output(self.tmux + ["split-window", "-d", "-P", "-F", "#{pane_id}"], text=True).strip()
        self.addCleanup(lambda: subprocess.run(self.tmux + ["kill-pane", "-t", other], check=False))
        self.assertEqual(self.lamp("get", "--pane", other).stdout.strip(), "unknown")
        self.assertNotEqual(self.lamp("set", "bad", "--pane", other, check=False).returncode, 0)
        self.assertNotEqual(self.lamp("set", "working", "--detail", "two\nlines", "--pane", other, check=False).returncode, 0)
        self.assertNotEqual(self.lamp("set", "working", "--detail", "#[fg=red]oops", "--pane", other, check=False).returncode, 0)
        self.assertEqual(self.lamp("get", "--pane", other).stdout.strip(), "unknown")
        self.assertNotEqual(self.lamp("get", "--pane", "%999999", check=False).returncode, 0)

    def test_reporter_and_unknown_are_distinct(self):
        self.lamp("disconnect")
        self.assertEqual(self.lamp("get", "--field", "connected").stdout.strip(), "0")
        self.lamp("connect")
        self.lamp("set", "unknown")
        self.assertEqual(self.lamp("get", "--field", "connected").stdout.strip(), "1")
        self.assertEqual(self.lamp("get", "--field", "state").stdout.strip(), "unknown")
        self.lamp("disconnect")
        self.lamp("set", "working")
        self.assertEqual(self.lamp("get", "--field", "connected").stdout.strip(), "1")

    def test_plugin_renders_each_panel_without_overwriting_theme(self):
        before = subprocess.check_output(self.tmux + ["show-options", "-w", "-v", "pane-border-format"], text=True).strip()
        subprocess.run([str(ROOT / "agent-adon.tmux")], env=self.env, check=True)
        after = subprocess.check_output(self.tmux + ["show-options", "-w", "-v", "pane-border-format"], text=True).strip()
        self.assertEqual(after, before)
        subprocess.run(self.tmux + ["resize-window", "-x", "120", "-y", "24"], check=True)
        for state, marker in [("working", "G"), ("waiting", "Y"), ("error", "R"), ("idle", "I"), ("unknown", None)]:
            self.lamp("set", state, "--name", "phone use")
            displayed = subprocess.check_output(self.tmux + ["display-message", "-p", "-t", self.pane, "#{E:@agent_adon_ascii_label_format}"], text=True)
            plain = re.sub(r"#\[[^]]*\]", "", displayed)
            if marker:
                self.assertIn(marker, plain)
            else:
                self.assertIn("g y r i", plain)
                self.assertNotIn("?", plain)
            self.assertIn("phone use", displayed)


if __name__ == "__main__":
    unittest.main()
