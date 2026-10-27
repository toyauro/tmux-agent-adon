"""Validate session binding without touching existing panels or processes."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("codex_bind", Path(__file__).with_name("bind.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
UUID = "00000000-0000-4000-8000-000000000001"


class BindTests(unittest.TestCase):
    def fake(self, *, panel="%7\t/dev/ttys111\t10\n", processes=None):
        writes = []
        rows = processes if processes is not None else " 11 ttys111 S+ /path/to/codex\n12 ttys112 S+ codex\n"
        def run(args):
            if args[0:2] == ["tmux", "display-message"]:
                return panel
            if args[:2] == ["ps", "-axo"]:
                return rows
            if args[:2] == ["ps", "-p"]:
                return "  Tue Oct  7 12:34:56 2026  \n"
            if args[:2] == ["tmux", "set-option"]:
                writes.append(args)
                return ""
            raise AssertionError(args)
        return run, writes

    def test_exact_foreground_binding_preserves_start_time(self):
        run, writes = self.fake()
        result = module.bind("%7", UUID, env={"TMUX": "test-socket,1,0"}, run=run)
        self.assertEqual(result["pid"], 11)
        self.assertEqual(result["start"], "Tue Oct  7 12:34:56 2026")
        self.assertEqual([a[-2] for a in writes], ["@agent_adon_session_id", "@agent_adon_session_pid", "@agent_adon_session_start", "@agent_adon_session_id"])
        self.assertEqual(writes[0][-1], "")
        self.assertTrue(all(a[4] == "%7" for a in writes))

    def test_stale_pane_fallback_cannot_bind(self):
        run, writes = self.fake(panel="%8\t/dev/ttys111\t10\n")
        with self.assertRaises(module.BindingError):
            module.bind("%7", UUID, env={"TMUX": "test"}, run=run)
        self.assertEqual(writes, [])

    def test_missing_or_ambiguous_foreground_codex_is_rejected(self):
        for rows in ["11 ttys111 S codex\n", "11 ttys111 Z+ codex\n", "11 ttys111 S+ codex\n13 ttys111 S+ codex\n"]:
            run, writes = self.fake(processes=rows)
            with self.subTest(rows=rows), self.assertRaises(module.BindingError):
                module.bind("%7", UUID, env={"TMUX": "test"}, run=run)
            self.assertEqual(writes, [])

    def test_no_server_or_invalid_session_has_no_writes(self):
        run, writes = self.fake()
        for env, session in [({}, UUID), ({"TMUX": "test"}, "not-a-session")]:
            with self.subTest(env=env), self.assertRaises(module.BindingError):
                module.bind("%7", session, env=env, run=run)
        self.assertEqual(writes, [])

    def test_replaced_process_is_not_bound(self):
        original, writes = self.fake()
        calls = 0
        def run(args):
            nonlocal calls
            if args[:2] == ["ps", "-p"]:
                calls += 1
                return "Tue Oct  7 12:34:56 2026" if calls == 1 else "Tue Oct  7 12:35:00 2026"
            return original(args)
        with self.assertRaises(module.BindingError):
            module.bind("%7", UUID, env={"TMUX": "test"}, run=run)
        self.assertEqual(writes, [])


if __name__ == "__main__":
    unittest.main()
