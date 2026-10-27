#!/usr/bin/env python3
"""Resolve a hook's real owning terminal before reporting panel state.

Hook execution may occur outside a tmux pane or inherit stale environment from
a shared daemon. A confirmed agent ancestor's terminal takes precedence over
TMUX_PANE. With no unambiguous owner, leave every panel untouched.
"""
import os
import json
from pathlib import Path
import subprocess
import sys


def owner_pane(agent, rows, ancestors, session=None):
    for command, tty in ancestors:
        if Path(command).name != agent:
            continue
        if tty in ("", "?", "??", "-"):
            continue
        matches = [row[0] for row in rows
                   if Path(row[1]).name == tty
                   and (session is None or row[2] == session)]
        return matches[0] if len(matches) == 1 else None
    return None


def bound_pane(agent, session_id, rows, inspect, session=None):
    """A shared daemon has no TTY; accept only an explicit live binding."""
    if agent != "codex" or not isinstance(session_id, str):
        return None
    matches = []
    for row in rows:
        if len(row) < 6 or row[3] != session_id or not row[4].isdigit():
            continue
        if session is not None and row[2] != session:
            continue
        process = inspect(row[4])
        if process is None:
            continue
        if (Path(process["command"]).name == agent
                and process["tty"] == Path(row[1]).name
                and "+" in process["stat"]
                and not any(flag in process["stat"] for flag in "ZX")
                and " ".join(process["start"].split()) == " ".join(row[5].split())):
            matches.append(row[0])
    return matches[0] if len(matches) == 1 else None


def inspect_process(pid):
    result = {}
    for field, name in [("comm", "command"), ("tty", "tty"), ("lstart", "start"), ("stat", "stat")]:
        call = subprocess.run(["ps", "-p", pid, "-o", field + "="],
                              capture_output=True, text=True, timeout=1, check=False)
        if call.returncode:
            return None
        result[name] = call.stdout.strip()
    return result


def main():
    if len(sys.argv) != 3:
        return
    agent, event = sys.argv[1:]
    reply = '{"decision":"stop"}' if (agent, event) == ("agy", "Stop") else "{}"
    diagnostic = {"agent": agent, "event": event}
    def record(status):
        destination = os.environ.get("ADON_DIAGNOSTICS")
        if destination:
            try:
                Path(destination).write_text(json.dumps({**diagnostic, "status": status}) + "\n")
            except OSError:
                pass
    try:
        if agent not in ("codex", "claude", "agy") or not os.environ.get("TMUX"):
            raise ValueError("no supported tmux context")
        tmux = os.environ.get("TMUX_BIN", "tmux")
        try:
            payload = json.load(sys.stdin)
            if not isinstance(payload, dict):
                payload = {}
        except (ValueError, OSError):
            payload = {}
        output = subprocess.run(
            [tmux, "list-panes", "-a", "-F", "#{pane_id}\t#{pane_tty}\t#{session_name}\t#{@agent_adon_session_id}\t#{@agent_adon_session_pid}\t#{@agent_adon_session_start}"],
            capture_output=True, text=True, timeout=1, check=True).stdout
        rows = [line.split("\t", 5) for line in output.splitlines()]
        rows = [row for row in rows if len(row) >= 3]
        ancestors = []
        parent = os.getppid()
        for _ in range(10):
            info = subprocess.run(
                ["ps", "-p", str(parent), "-o", "ppid=,tty=,comm="],
                capture_output=True, text=True, timeout=1, check=True).stdout.strip().split(None, 2)
            if len(info) != 3:
                break
            parent = int(info[0])
            ancestors.append((info[2], info[1]))
            if parent <= 1:
                break
        pane = owner_pane(agent, rows, ancestors, os.environ.get("ADON_SESSION"))
        if pane is None:
            pane = bound_pane(agent, payload.get("session_id"), rows,
                              inspect_process, os.environ.get("ADON_SESSION"))
        diagnostic["ancestors"] = [(Path(command).name, tty) for command, tty in ancestors]
        diagnostic["pane"] = pane
        if pane is None:
            raise ValueError("agent terminal cannot be confirmed")
        env = dict(os.environ, TMUX_PANE=pane)
        bridge = Path(__file__).with_name("lamp-hook.py")
        subprocess.run([sys.executable, str(bridge), agent, event], env=env,
                       input=json.dumps(payload), text=True, timeout=3, check=False)
        record("forwarded")
        return
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        record(str(error))
    print(reply)


if __name__ == "__main__":
    main()
