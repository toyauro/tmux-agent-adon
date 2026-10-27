"""Exercise the mouse menu on an isolated tmux server and PTY."""
import fcntl
import os
from pathlib import Path
import pty
import struct
import subprocess
import termios
import time
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]


class MouseMenuTest(unittest.TestCase):
    def setUp(self):
        self.tmux = [os.environ.get("TMUX_BIN", "tmux"), "-L", "adon-menu-test-" + uuid.uuid4().hex[:10]]
        subprocess.run(self.tmux + ["-f", "/dev/null", "new", "-d", "-s", "test", "-x", "80", "-y", "20"], check=True)
        self.left = self.query("display", "-p", "#{pane_id}")
        self.right = self.query("split-window", "-h", "-d", "-P", "-F", "#{pane_id}")
        socket = self.query("display", "-p", "#{socket_path},#{pid},0")
        self.env = dict(os.environ, TMUX=socket, TMUX_PANE=self.left, TERM="xterm-256color")
        self.master = None
        self.client = None

    def tearDown(self):
        subprocess.run(self.tmux + ["kill-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if self.client:
            try:
                self.client.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.client.kill()
                self.client.wait()
        if self.master is not None:
            os.close(self.master)

    def query(self, *args):
        return subprocess.check_output(self.tmux + list(args), text=True).strip()

    def option(self, pane, key):
        return subprocess.run(self.tmux + ["show-options", "-p", "-v", "-t", pane, key], capture_output=True, text=True).stdout.rstrip("\n")

    def test_button_targets_clicked_panel_and_rename_escapes(self):
        if self.query("display", "-p", "#{version}").startswith("3.6"):
            self.skipTest("tmux 3.6 has no border mouse-control key")
        subprocess.run([str(ROOT / "agent-adon.tmux")], env=self.env, check=True)
        for args in (["set", "-g", "mouse", "on"], ["set", "-w", "pane-border-status", "top"], ["set", "-w", "pane-border-format", "#{E:@agent_adon_label_format}"]):
            subprocess.run(self.tmux + args, check=True)
        subprocess.run(self.tmux + ["set-option", "-p", "-t", self.right, "@agent_adon_detail", "old"], check=True)
        subprocess.run(self.tmux + ["set-option", "-p", "-t", self.right, "@agent_adon_updated", "123"], check=True)
        master, slave = pty.openpty()
        self.master = master
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 20, 80, 0, 0))
        self.client = subprocess.Popen(self.tmux + ["attach", "-t", "test"], stdin=slave, stdout=slave, stderr=slave, env=dict(os.environ, TERM="xterm-256color"))
        os.close(slave)
        time.sleep(0.7)
        def click_button():
            # Button is right-aligned on the top border of the right panel.
            os.write(master, b"\x1b[<0;80;1M\x1b[<0;80;1m")
            time.sleep(0.25)
        click_button()
        os.write(master, b"g")
        time.sleep(0.4)
        self.assertEqual(self.option(self.right, "@agent_adon_state"), "working")
        self.assertEqual(self.option(self.left, "@agent_adon_state"), "")
        self.assertEqual(self.option(self.right, "@agent_adon_detail"), "")
        self.assertEqual(self.option(self.right, "@agent_adon_updated"), "")
        click_button()
        os.write(master, b"n")
        time.sleep(0.25)
        name = "bob\"; set-option -g @pwn yes; # \\ ' end"
        os.write(master, name.encode() + b"\r")
        time.sleep(0.5)
        self.assertEqual(self.option(self.right, "@pane_name"), name)
        self.assertEqual(self.option(self.left, "@pane_name"), "")
        self.assertNotEqual(subprocess.run(self.tmux + ["show-options", "-g", "-v", "@pwn"], capture_output=True).returncode, 0)

    def test_conflicting_mouse_binding_is_not_overwritten(self):
        if self.query("display", "-p", "#{version}").startswith("3.6"):
            self.skipTest("tmux 3.6 has no border mouse-control key")
        subprocess.run(self.tmux + ["bind-key", "-n", "MouseDown1Control1", "display-message", "existing"], check=True)
        before = self.query("list-keys", "-T", "root", "MouseDown1Control1")
        proc = subprocess.run([str(ROOT / "agent-adon.tmux")], env=self.env, capture_output=True, text=True, check=True)
        after = self.query("list-keys", "-T", "root", "MouseDown1Control1")
        self.assertEqual(before, after)
        self.assertIn("already bound", proc.stderr)
        self.assertEqual(self.query("show-options", "-g", "-v", "@agent_adon_controls_available"), "0")
        self.assertNotIn("range=control|1", self.query("display", "-p", "#{E:@agent_adon_indicator_format}"))

    def test_keyboard_fallback_on_old_server_or_mouse_conflict(self):
        result = subprocess.run([str(ROOT / "agent-adon.tmux")], env=self.env, capture_output=True, text=True, check=True)
        self.assertEqual(self.query("show-options", "-g", "-v", "@agent_adon_keyboard_available"), "1")
        if self.query("display", "-p", "#{version}").startswith("3.6"):
            self.assertIn("prefix + a", result.stderr)
            self.assertEqual(self.query("show-options", "-g", "-v", "@agent_adon_controls_available"), "0")
            self.assertNotIn("range=control|1", self.query("display", "-p", "#{E:@agent_adon_indicator_format}"))
        else:
            self.assertEqual(self.query("show-options", "-g", "-v", "@agent_adon_controls_available"), "1")
            self.assertIn("range=control|1", self.query("display", "-p", "#{E:@agent_adon_indicator_format}"))
        subprocess.run(self.tmux + ["select-pane", "-t", self.right], check=True)
        master, slave = pty.openpty()
        self.master = master
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 20, 80, 0, 0))
        self.client = subprocess.Popen(self.tmux + ["attach", "-t", "test"], stdin=slave, stdout=slave, stderr=slave, env=dict(os.environ, TERM="xterm-256color"))
        os.close(slave)
        time.sleep(0.7)
        os.write(master, b"\x02a")
        time.sleep(0.3)
        os.write(master, b"g")
        time.sleep(0.5)
        self.assertEqual(self.option(self.right, "@agent_adon_state"), "working")
        self.assertEqual(self.option(self.left, "@agent_adon_state"), "")
        os.write(master, b"\x02a")
        time.sleep(0.3)
        os.write(master, b"n")
        time.sleep(0.3)
        name = "agent \"quoted\"; set-option -g @pwn yes"
        os.write(master, name.encode() + b"\r")
        time.sleep(0.6)
        self.assertEqual(self.option(self.right, "@pane_name"), name)
        self.assertEqual(self.option(self.left, "@pane_name"), "")
        self.assertNotEqual(subprocess.run(self.tmux + ["show-options", "-g", "-v", "@pwn"], capture_output=True).returncode, 0)

    def test_prefix_conflict_is_not_overwritten(self):
        if not self.query("display", "-p", "#{version}").startswith("3.6"):
            subprocess.run(self.tmux + ["bind-key", "-n", "MouseDown1Control1", "display-message", "existing mouse"], check=True)
        subprocess.run(self.tmux + ["bind-key", "-T", "prefix", "a", "display-message", "existing prefix"], check=True)
        before = self.query("list-keys", "-T", "prefix", "a")
        result = subprocess.run([str(ROOT / "agent-adon.tmux")], env=self.env, capture_output=True, text=True, check=True)
        self.assertIn("prefix + a is already bound", result.stderr)
        self.assertEqual(before, self.query("list-keys", "-T", "prefix", "a"))
        self.assertEqual(self.query("show-options", "-g", "-v", "@agent_adon_controls_available"), "0")

    def test_prefix_conflict_preserved_while_mouse_still_works(self):
        if self.query("display", "-p", "#{version}").startswith("3.6"):
            self.skipTest("tmux 3.6 has no border mouse-control key")
        subprocess.run(self.tmux + ["bind-key", "-T", "prefix", "a", "display-message", "existing prefix"], check=True)
        before = self.query("list-keys", "-T", "prefix", "a")
        result = subprocess.run([str(ROOT / "agent-adon.tmux")], env=self.env, capture_output=True, text=True, check=True)
        self.assertIn("prefix + a is already bound", result.stderr)
        self.assertEqual(before, self.query("list-keys", "-T", "prefix", "a"))
        self.assertEqual(self.query("show-options", "-g", "-v", "@agent_adon_controls_available"), "1")
        self.assertEqual(self.query("show-options", "-g", "-v", "@agent_adon_keyboard_available"), "0")


if __name__ == "__main__":
    unittest.main()
