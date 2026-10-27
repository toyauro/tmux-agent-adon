#!/usr/bin/env python3
"""Translate Antigravity's public statusLine JSON into panel state.

No payload is persisted or printed. Configure stack_with_default=true to retain
Antigravity's built-in status line; this script deliberately prints nothing.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def state_for(payload):
    """Use harness-provided state, never infer state from conversation text."""
    if payload.get("tool_confirmation_pending") is True:
        return "waiting"
    state = payload.get("agent_state")
    if state == "idle":
        count = payload.get("task_count", 0)
        return "working" if isinstance(count, (int, float)) and count > 0 else "idle"
    if state in ("working", "tool_use", "reviewing", "initializing"):
        return "working"
    if state == "authenticating":
        return "waiting"
    if state == "error":
        return "error"
    return "unknown"


def main():
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            return
        pane = os.environ.get("TMUX_PANE", "")
        if not os.environ.get("TMUX") or not re.fullmatch(r"%[0-9]+", pane):
            return
        lamp = os.environ.get("LAMP_BIN") or str(Path(__file__).resolve().parents[2] / "bin" / "lamp")
        state = state_for(payload)
        if state == "unknown":
            commands = [[lamp, "connect", "--pane", pane], [lamp, "set", "unknown", "--pane", pane, "--detail", "Antigravity state unknown"]]
        else:
            commands = [[lamp, "set", state, "--pane", pane, "--detail", "Antigravity " + state]]
        for args in commands:
            subprocess.run(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=2, check=False)
    except (ValueError, OSError, subprocess.SubprocessError):
        # A lamp failure must not disable the Agent's status line or its work.
        pass


if __name__ == "__main__":
    main()
