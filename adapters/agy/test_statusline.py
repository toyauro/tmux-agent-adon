import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil
import uuid
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('statusline.py')
spec = importlib.util.spec_from_file_location('adon_agy_statusline', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class StatusLineTests(unittest.TestCase):
    def test_native_states_and_background_work(self):
        for native, expected in [('idle','idle'),('working','working'),('tool_use','working'),('reviewing','working'),('initializing','working'),('authenticating','waiting'),('error','error'),('future_state','unknown')]:
            self.assertEqual(module.state_for({'agent_state':native}), expected)
        self.assertEqual(module.state_for({'agent_state':'idle','task_count':2}), 'working')
        self.assertEqual(module.state_for({'agent_state':'working','tool_confirmation_pending':True}), 'waiting')

    def test_payload_is_not_printed_or_logged(self):
        with tempfile.TemporaryDirectory() as d:
            lamp = Path(d)/'lamp'
            log = Path(d)/'calls.jsonl'
            lamp.write_text('#!'+sys.executable+'\nimport json,sys\nwith open('+repr(str(log))+',"a") as f: f.write(json.dumps(sys.argv[1:])+"\\n")\n')
            lamp.chmod(0o700)
            env = dict(os.environ, TMUX='/tmp/test,1,0', TMUX_PANE='%3', LAMP_BIN=str(lamp))
            result = subprocess.run([sys.executable,str(SCRIPT)], input=json.dumps({'agent_state':'idle','email':'private@example.com','cwd':'/private/work'}), text=True, env=env, capture_output=True, check=True)
            self.assertEqual(result.stdout,'')
            self.assertEqual(result.stderr,'')
            self.assertEqual(json.loads(log.read_text()), ['set','idle','--pane','%3','--detail','Antigravity idle'])

    def test_unknown_connects_reporter_and_outside_tmux_is_noop(self):
        with tempfile.TemporaryDirectory() as d:
            lamp=Path(d)/'lamp';log=Path(d)/'calls'
            lamp.write_text('#!'+sys.executable+'\nimport json,sys\nwith open('+repr(str(log))+',"a") as f: f.write(json.dumps(sys.argv[1:])+"\\n")\n');lamp.chmod(0o700)
            env=dict(os.environ,TMUX='/tmp/test,1,0',TMUX_PANE='%9',LAMP_BIN=str(lamp))
            subprocess.run([sys.executable,str(SCRIPT)], input='{}', text=True, env=env, check=True)
            self.assertEqual(json.loads(log.read_text().splitlines()[0]), ['connect','--pane','%9'])
            before=log.read_text();env.pop('TMUX',None)
            subprocess.run([sys.executable,str(SCRIPT)], input='{}', text=True, env=env, check=True)
            self.assertEqual(log.read_text(),before)

    @unittest.skipUnless(shutil.which("tmux"), "tmux is required")
    def test_real_tmux_state_and_script_hot_update(self):
        # The real harness invokes this short-lived script on every state
        # change. This checks its real CLI/tmux path and proves no cached
        # adapter process prevents a new mapping from taking effect.
        server = "adon-agy-test-" + uuid.uuid4().hex[:10]
        tmux = ["tmux", "-L", server]
        try:
            subprocess.run(tmux + ["-f", "/dev/null", "new-session", "-d", "-s", "test"], check=True)
            pane = subprocess.check_output(tmux + ["display-message", "-p", "#{pane_id}"], text=True).strip()
            context = subprocess.check_output(tmux + ["display-message", "-p", "#{socket_path},#{pid},0"], text=True).strip()
            env = dict(os.environ, TMUX=context, TMUX_PANE=pane,
                       LAMP_BIN=str(SCRIPT.parents[2] / "bin" / "lamp"))
            with tempfile.TemporaryDirectory() as directory:
                copied = Path(directory) / "statusline.py"
                copied.write_text(SCRIPT.read_text())
                def run():
                    subprocess.run([sys.executable, str(copied)], input='{"agent_state":"idle"}',
                                   text=True, env=env, check=True)
                    return subprocess.check_output(tmux + ["show-options", "-p", "-t", pane,
                                                          "-v", "@agent_adon_state"], text=True).strip()
                self.assertEqual(run(), "idle")
                self.assertEqual(subprocess.check_output(tmux + ["show-options", "-p", "-t", pane,
                                                                 "-v", "@agent_adon_connected"], text=True).strip(), "1")
                copied.write_text(copied.read_text().replace('else "idle"', 'else "waiting"'))
                self.assertEqual(run(), "waiting")
        finally:
            subprocess.run(tmux + ["kill-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def test_malformed_input_and_missing_cli_do_not_fail(self):
        env=dict(os.environ,TMUX='/tmp/test,1,0',TMUX_PANE='%9',LAMP_BIN='/nonexistent/lamp')
        for data in ['not json', '[]', '{"agent_state":"working"}']:
            result=subprocess.run([sys.executable,str(SCRIPT)],input=data,text=True,env=env,capture_output=True)
            self.assertEqual(result.returncode,0)
            self.assertEqual(result.stdout,'')
            self.assertEqual(result.stderr,'')


if __name__=='__main__':unittest.main()
