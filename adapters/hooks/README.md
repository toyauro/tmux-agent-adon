# Optional Claude Code, Codex, and Antigravity hooks

These are opt-in examples. They do **not** install themselves or alter any
existing agent configuration. Set `LAMP_HOOK` to this directory's absolute
`lamp-hook.py` path and put `lamp` on `PATH` (or set `LAMP_BIN` to its absolute
path) in the environment that launches the agent. Python 3 is required.
The hook uses `TMUX_PANE`; outside tmux it does nothing. Test it in a disposable
session before using it in a live one.

Merge the event entries from `claude.example.json` into `~/.claude/settings.json`
or project settings; merge `codex.example.json` into an appropriate
`~/.codex/hooks.json` or project `.codex/hooks.json`; merge the named hook in
`agy.example.json` into `~/.gemini/config/hooks.json` or project
`.agents/hooks.json`. **Do not replace existing hooks or settings.** Check the
agent's documented hook-trust/enablement requirements. Exact events vary by
agent version and execution surface; configuration examples have not been
verified against a live session. `agy-y` is an alias for `agy` in the originating
environment, not a separate adapter.

The hook updates only the current panel and uses fixed status descriptions. It
never logs, echoes, or sends prompts or tool arguments to `lamp`. Some events
require parsing a JSON payload in memory for a status field. It does not approve
or deny requests, change a prompt, stop, or continue the agent. Updates are
best effort and the `lamp` call times out after one second.

## Conservative event mapping

| Agent | Event | Lamp | Meaning and limits |
| --- | --- | --- | --- |
| Claude / Codex | `UserPromptSubmit` | working | A prompt was submitted, not proof the task finished. |
| Claude / Codex | `PermissionRequest` | waiting | A permission decision is being requested; another hook may answer automatically. |
| Claude / Codex | `PostToolUse` | working | Work resumed after a tool, including a failed tool. |
| Claude | `PostToolUseFailure` | working | An individual failed tool is not necessarily a blocked task. |
| Claude | `StopFailure` | error | An API error ended the response; not a general business-task failure. |
| Claude | `Notification` `idle_prompt` | idle | Documented delayed idle signal; may never fire if the user types or a background agent is active. |
| Claude / Codex | `Stop` | unknown | Stop hooks can request another continuation; no guarantee of idle or success. |
| Codex | `Interrupt` | unknown | Execution state no longer confirmed. |
| Claude / Codex | `SessionEnd` | disconnected | A normal session end clears the reporter; forced termination may skip the hook. |
| Antigravity | `PreInvocation` | working | The model is about to run. |
| Antigravity | selected `PreToolUse` | waiting | Only `ask_question` / `ask_permission`, not every possible wait. |
| Antigravity | `PostToolUse` | working | Work proceeds after a tool, including an unsuccessful tool. |
| Antigravity | `Stop` with `terminationReason=error` | error | System execution error. |
| Antigravity | other `Stop` | unknown | Another hook may continue, including when `fullyIdle` was true. |

`PermissionRequest` happens before a decision, and other hooks may immediately
approve or deny it. Post-tool events or the next prompt normally restore working,
but denied prompts may not emit a post-tool event; the lamp can temporarily be
stale. These adapters do not recognize every kind of user input or network wait.
The four colors represent panel status, not task success. Use the CLI directly
when an agent knows it is blocked or actually waiting. A forced kill or a
disconnected environment may not send any cleanup event.

Sources: [Claude Code hooks](https://code.claude.com/docs/en/hooks),
[Codex hooks](https://learn.chatgpt.com/docs/hooks),
[Antigravity hooks](https://antigravity.google/docs/hooks/).
