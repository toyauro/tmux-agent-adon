import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
HOOK = HERE / "lamp-hook.py"


class HookTests(unittest.TestCase):
    def run_hook(self, agent, event, payload, pane="%1"):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            output = temp / "calls.json"
            fake = temp / "lamp"
            fake.write_text(
                "#!" + sys.executable + "\n"
                "import json, os, pathlib, sys\n"
                "pathlib.Path(os.environ['HOOK_TEST_OUTPUT']).write_text(json.dumps(sys.argv[1:]))\n"
            )
            fake.chmod(0o700)
            env = dict(os.environ, TMUX_PANE=pane, LAMP_BIN=str(fake), HOOK_TEST_OUTPUT=str(output))
            result = subprocess.run(
                [sys.executable, str(HOOK), agent, event],
                input=json.dumps(payload), text=True, capture_output=True, env=env,
                timeout=3, check=True,
            )
            return json.loads(result.stdout), json.loads(output.read_text()) if output.exists() else None

    def test_prompt_starts_work_without_echoing_secrets(self):
        result, call = self.run_hook("codex", "UserPromptSubmit", {"prompt": "secret prompt"})
        self.assertEqual(result, {})
        self.assertEqual(call, ["set", "working", "--detail", "Codex processing"])
        self.assertNotIn("secret", repr((result, call)))

    def test_stop_never_claims_success(self):
        for agent in ("codex", "claude", "agy"):
            with self.subTest(agent=agent):
                result, call = self.run_hook(agent, "Stop", {"fullyIdle": True})
                self.assertEqual(call[1], "unknown")
                self.assertEqual(result, {"decision": "stop"} if agent == "agy" else {})

    def test_claude_idle_and_failure_are_distinct(self):
        _, call = self.run_hook("claude", "Notification", {"notification_type": "idle_prompt"})
        self.assertEqual(call[1], "idle")
        _, call = self.run_hook("claude", "StopFailure", {"error": "private detail"})
        self.assertEqual(call[1], "error")
        self.assertNotIn("private detail", repr(call))

    def test_agy_question_and_error(self):
        _, call = self.run_hook("agy", "PreToolUse", {"toolCall": {"name": "ask_question", "args": {"question": "private"}}})
        self.assertEqual(call[1], "waiting")
        self.assertNotIn("private", repr(call))
        _, call = self.run_hook("agy", "Stop", {"terminationReason": "error", "error": "private"})
        self.assertEqual(call[1], "error")

    def test_outside_tmux_noop(self):
        result, call = self.run_hook("codex", "UserPromptSubmit", {}, pane="")
        self.assertEqual(result, {})
        self.assertIsNone(call)

    def test_session_end_disconnects_without_affecting_agent(self):
        for agent in ("claude", "codex"):
            with self.subTest(agent=agent):
                result, call = self.run_hook(agent, "SessionEnd", {"private": "do not print"})
                self.assertEqual(result, {})
                self.assertEqual(call, ["disconnect"])
                self.assertNotIn("private", repr((result, call)))
                result, call = self.run_hook(agent, "SessionEnd", {}, pane="")
                self.assertEqual(result, {})
                self.assertIsNone(call)

    def test_session_end_tolerates_missing_lamp(self):
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ, TMUX_PANE="%1", LAMP_BIN=str(Path(directory) / "missing"))
            result = subprocess.run([sys.executable, str(HOOK), "codex", "SessionEnd"],
                                    input="{}", text=True, capture_output=True, env=env,
                                    timeout=3, check=True)
            self.assertEqual(json.loads(result.stdout), {})

    def test_configs_are_json(self):
        for config in HERE.glob("*.example.json"):
            with self.subTest(config=config.name):
                self.assertIsInstance(json.loads(config.read_text()), dict)


if __name__ == "__main__":
    unittest.main()
