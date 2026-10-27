# Optional Claude Code, Codex, and Antigravity hooks

These are opt-in examples. They do **not** install themselves or alter any
existing agent configuration. Set `LAMP_HOOK` to this directory's absolute
`lamp-hook.py` path. The bridge locates this checkout's `bin/lamp` by default;
`LAMP_BIN` can override it. Python 3 is required.
The direct bridge uses `TMUX_PANE`; outside tmux it does nothing. A shared
background process can inherit a stale pane ID. Use the ownership-checking
`tmux-hook.py` dispatcher and the [Codex binding guide](../codex/README.md)
when events do not originate in the interactive terminal. Test the setup in
a disposable session before using it in a live one.

Merge the event entries from `claude.example.json` into `~/.claude/settings.json`
or project settings; merge `codex.example.json` into an appropriate
`~/.codex/hooks.json` or project `.codex/hooks.json`; merge the named hook in
`agy.example.json` into `~/.gemini/config/hooks.json` or project
`.agents/hooks.json`. **Do not replace existing hooks or settings.** Check the
agent's documented hook-trust/enablement requirements. Exact events vary by
agent version and execution surface. Claude Code 2.1.258 has been verified in
a live isolated TUI: adding these hooks to its user settings while running
loaded them without a restart; a real prompt produced working then idle, and
normal exit disconnected the reporter. Codex and Antigravity validation may
require their own version-specific setup. `agy-y` is an alias for `agy` in the originating
environment, not a separate adapter.

The hook updates only the current panel and uses fixed status descriptions. It
never logs, echoes, or sends prompts or tool arguments to `lamp`. Some events
require parsing a JSON payload in memory for a status field. It does not approve
or deny requests, change a prompt, stop, or continue the agent. Updates are
best effort and the `lamp` call times out after one second.

## Conservative event mapping

| Agent | Event | Lamp | Meaning and limits |
| --- | --- | --- | --- |
| Claude | `SessionStart` | connected / idle | The reporter is ready; this is not a task result. |
| Claude / Codex | `UserPromptSubmit` | working | A prompt was submitted, not proof the task finished. |
| Claude | `PreToolUse` | working | Work resumes before a tool, including a continuation after Stop. |
| Claude / Codex | `PermissionRequest` | waiting | A permission decision is being requested; another hook may answer automatically. |
| Claude / Codex | `PostToolUse` | working | Work resumed after a tool, including a failed tool. |
| Claude | `PostToolUseFailure` | working | An individual failed tool is not necessarily a blocked task. |
| Claude | `StopFailure` | error | An API error ended the response; not a general business-task failure. |
| Claude | `Notification` `idle_prompt` | idle | Documented delayed idle signal; may never fire if the user types or a background agent is active. |
| Claude | `Stop` | idle | The current response stopped; this does not assert task success. A later prompt or tool event restores working. |
| Codex | `SessionStart` | idle | Activity hint that the session started; not a task result. |
| Codex | `PreToolUse` | working | A tool event indicates work, when this hook is configured. |
| Codex | `Stop` | idle | Provisional activity hint: another hook may continue, so it does not establish final idle or success. |
| Codex | `Interrupt` | idle | Reports an interrupted turn, not its task outcome. |
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
Codex `Stop` can briefly show idle while continuation is pending; a later prompt
or configured tool event updates it. Existing shared-daemon sessions require an
explicit verified binding; they are not automatically discovered.
The four colors represent panel status, not task success. Use the CLI directly
when an agent knows it is blocked or actually waiting. A forced kill or a
disconnected environment may not send any cleanup event.

Sources: [Claude Code hooks](https://code.claude.com/docs/en/hooks),
[Codex hooks](https://learn.chatgpt.com/docs/hooks),
[Antigravity hooks](https://antigravity.google/docs/hooks/).
