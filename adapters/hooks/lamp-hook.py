#!/usr/bin/env python3
"""Best-effort, opt-in hook bridge. Never controls the Agent's execution."""

import json
import os
import subprocess
import sys


def state_for(agent, event, payload):
    """Only map signals whose meaning is documented; no inference from text."""
    if agent == "claude":
        if event == "UserPromptSubmit":
            return "working", "Claude processing"
        if event == "PermissionRequest":
            return "waiting", "Claude permission request"
        if event in ("PostToolUse", "PostToolUseFailure"):
            return "working", "Claude processing"
        if event == "StopFailure":
            return "error", "Claude API error"
        if event == "Stop":
            # Stop hooks can make the agent continue; background work may run.
            return "unknown", "Claude stop observed"
        if event == "Notification" and payload.get("notification_type") == "idle_prompt":
            return "idle", "Claude idle prompt"
    elif agent == "codex":
        if event == "UserPromptSubmit":
            return "working", "Codex processing"
        if event == "PermissionRequest":
            return "waiting", "Codex permission request"
        if event == "PostToolUse":
            return "working", "Codex processing"
        if event in ("Stop", "Interrupt"):
            # Stop may request a continuation; Interrupt is not success.
            return "unknown", "Codex " + event.lower()
    elif agent == "agy":
        if event == "PreInvocation":
            return "working", "Antigravity processing"
        if event in ("PreToolUse", "PostToolUse"):
            tool = payload.get("toolCall")
            tool = tool.get("name") if isinstance(tool, dict) else None
            if event == "PreToolUse" and tool in ("ask_question", "ask_permission"):
                return "waiting", "Antigravity input requested"
            if event == "PostToolUse":
                return "working", "Antigravity processing"
        if event == "Stop":
            if payload.get("terminationReason") == "error":
                return "error", "Antigravity execution error"
            # Other Stop hooks may continue; do not promise idle.
            return "unknown", "Antigravity stop observed"
    return None


def main():
    if len(sys.argv) != 3:
        return
    agent, event = sys.argv[1:]
    # These events need one fixed metadata field only. Never persist or echo the
    # remaining payload, which can contain prompts, paths, or tool arguments.
    payload = {}
    if (agent, event) in {
        ("claude", "Notification"), ("agy", "Stop"),
        ("agy", "PreToolUse"), ("agy", "PostToolUse"),
    }:
        try:
            payload = json.load(sys.stdin)
            if not isinstance(payload, dict):
                payload = {}
        except (ValueError, OSError):
            payload = {}

    state = state_for(agent, event, payload)
    # A normal SessionEnd means the reporter has disconnected; unlike Stop,
    # it should turn off the dim powered lights as well as clearing state.
    disconnect = agent in ("claude", "codex") and event == "SessionEnd"
    if (state or disconnect) and os.environ.get("TMUX_PANE"):
        try:
            args = ["disconnect"] if disconnect else ["set", state[0], "--detail", state[1]]
            subprocess.run(
                [os.environ.get("LAMP_BIN", "lamp"), *args],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, timeout=1, check=False,
            )
        except (OSError, subprocess.SubprocessError):
            pass

    # Hooks are observers: never approve, deny, continue, or print input.
    # Antigravity's Stop schema requires decision; any non-continue allows stop.
    print('{"decision":"stop"}' if agent == "agy" and event == "Stop" else "{}")


if __name__ == "__main__":
    main()
