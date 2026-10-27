import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("tmux_hook", Path(__file__).with_name("tmux-hook.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class OwnerTest(unittest.TestCase):
    def test_uses_terminal_even_when_inherited_pane_would_be_wrong(self):
        rows = [["%1", "/dev/ttys001", "vibe"], ["%2", "/dev/ttys002", "vibe"]]
        self.assertEqual(module.owner_pane("codex", rows, [("/bin/sh", "??"), ("/opt/codex", "ttys002")]), "%2")

    def test_no_guess_for_daemon_or_wrong_session(self):
        rows = [["%1", "/dev/ttys001", "other"]]
        self.assertIsNone(module.owner_pane("codex", rows, [("codex", "??")]))
        self.assertIsNone(module.owner_pane("codex", rows, [("codex", "ttys001")], "vibe"))

    def test_rejects_duplicate_or_unrelated_owner(self):
        rows = [["%1", "/dev/ttys001", "vibe"], ["%2", "/dev/ttys001", "vibe"]]
        self.assertIsNone(module.owner_pane("claude", rows, [("claude", "ttys001")]))
        self.assertIsNone(module.owner_pane("claude", rows, [("node", "ttys001")]))

    def test_daemon_binding_requires_same_live_session_process(self):
        rows = [["%2", "/dev/ttys002", "vibe", "session-a", "123", "Wed Oct 28 00:00:00 2026"]]
        live = {"command": "/opt/bin/codex", "tty": "ttys002", "stat": "S+", "start": "Wed Oct 28 00:00:00 2026"}
        self.assertEqual(module.bound_pane("codex", "session-a", rows, lambda pid: live, "vibe"), "%2")
        self.assertIsNone(module.bound_pane("codex", "other-session", rows, lambda pid: live, "vibe"))
        live["start"] = "Wed Oct 28 00:01:00 2026"
        self.assertIsNone(module.bound_pane("codex", "session-a", rows, lambda pid: live, "vibe"))
        live["start"] = "Wed Oct 28 00:00:00 2026"
        live["stat"] = "Z+"
        self.assertIsNone(module.bound_pane("codex", "session-a", rows, lambda pid: live, "vibe"))

    def test_daemon_binding_does_not_follow_dead_or_background_agent(self):
        rows = [["%2", "/dev/ttys002", "vibe", "session-a", "123", "start"]]
        self.assertIsNone(module.bound_pane("codex", "session-a", rows, lambda pid: None, "vibe"))
        live = {"command": "codex", "tty": "ttys002", "stat": "S", "start": "start"}
        self.assertIsNone(module.bound_pane("codex", "session-a", rows, lambda pid: live, "vibe"))


if __name__ == "__main__":
    unittest.main()
