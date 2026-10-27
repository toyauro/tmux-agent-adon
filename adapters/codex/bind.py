#!/usr/bin/env python3
"""Bind a known native Codex session ID to one verified foreground panel."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import uuid


class BindingError(RuntimeError):
    pass


def output(args):
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.PIPE, timeout=3)
    except (OSError, subprocess.SubprocessError) as exc:
        raise BindingError("unable to verify local tmux/process metadata") from exc


def panel_metadata(pane, run=output):
    # display-message can fall back to another pane for a stale target: compare
    # its actual ID, rather than trusting command success.
    values = run(["tmux", "display-message", "-p", "-t", pane,
                  "#{pane_id}\t#{pane_tty}\t#{pane_pid}"]).strip().split("\t")
    if len(values) != 3 or values[0] != pane or not values[1].startswith("/dev/"):
        raise BindingError("target pane is missing or has no verifiable terminal")
    return tuple(values)


def foreground_codex(tty, run=output):
    rows = run(["ps", "-axo", "pid=,tty=,stat=,comm="]).splitlines()
    matches = []
    for row in rows:
        columns = row.strip().split(None, 3)
        if len(columns) != 4:
            continue
        pid, process_tty, state, command = columns
        if (process_tty == Path(tty).name and Path(command).name == "codex"
                and "+" in state and not any(flag in state for flag in "ZX")):
            if pid.isdigit():
                matches.append(pid)
    if len(matches) != 1:
        raise BindingError("target terminal must have exactly one live foreground Codex process")
    return matches[0]


def start_time(pid, run=output):
    value = run(["ps", "-p", pid, "-o", "lstart="]).strip()
    if not value or "\n" in value:
        raise BindingError("Codex process start time is unavailable")
    return value


def bind(pane, session_id, *, env=None, run=output):
    env = os.environ if env is None else env
    if not env.get("TMUX"):
        raise BindingError("TMUX must select the intended running tmux server")
    if not re.fullmatch(r"%[0-9]+", pane):
        raise BindingError("pane must be an explicit tmux ID such as %3")
    try:
        if str(uuid.UUID(session_id)) != session_id.lower():
            raise ValueError("not canonical")
    except (ValueError, AttributeError) as exc:
        raise BindingError("session ID must be a canonical UUID from Codex /status") from exc
    session_id = session_id.lower()
    initial = panel_metadata(pane, run)
    pid = foreground_codex(initial[1], run)
    started = start_time(pid, run)
    # A terminal can change while being inspected. Recheck before committing
    # a mapping, and publish the session ID last so readers can reject an old
    # PID/start-time pair. This does not identify a session by guessing cwd.
    if panel_metadata(pane, run) != initial or foreground_codex(initial[1], run) != pid or start_time(pid, run) != started:
        raise BindingError("target changed while verifying; retry the bind")
    for key, value in [("@agent_adon_session_id", ""),
                       ("@agent_adon_session_pid", pid),
                       ("@agent_adon_session_start", started),
                       ("@agent_adon_session_id", session_id)]:
        run(["tmux", "set-option", "-p", "-t", pane, key, value])
    return {"pane": pane, "pid": int(pid), "start": started, "session_id": session_id}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pane", required=True)
    parser.add_argument("--session-id", required=True)
    args = parser.parse_args()
    try:
        result = bind(args.pane, args.session_id)
    except BindingError as exc:
        parser.exit(2, "adon codex bind: " + str(exc) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
