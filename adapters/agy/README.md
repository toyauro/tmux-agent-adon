# Antigravity CLI: native status signal

This adapter consumes Antigravity's public `statusLine` JSON rather than
reconstructing state from its terminal output or transcript. `agy-y` is an
alias for `agy` in some environments; both use the same adapter.

## Attach to a running agent

In an idle Antigravity CLI panel with an empty input field, run this native
slash command, substituting the actual installation path:

```text
/statusline /absolute/path/to/python3 /absolute/path/to/tmux-agent-adon/adapters/agy/statusline.py
```

The CLI's documented `/statusline <command>` interface immediately installs
the command without restarting the agent. The script prints no status text.
To keep Antigravity's own status line visible, set `stack_with_default: true`
in the existing `statusLine` object in `~/.gemini/antigravity-cli/settings.json`,
preserving its other fields and all other settings. A pre-existing custom
status command must be deliberately composed with this adapter, not silently
replaced.

For new sessions the corresponding configuration is:

```json
{
  "statusLine": {
    "type": "command",
    "command": "/absolute/path/to/python3 /absolute/path/to/tmux-agent-adon/adapters/agy/statusline.py",
    "enabled": true,
    "stack_with_default": true
  }
}
```

The CLI executes the script again on state changes, so editing this file's
mapping takes effect on its next invocation; no agent restart is needed.
The default `lamp` path is resolved relative to this repository. `LAMP_BIN`
can override it. The active process must have the correct `TMUX` and
`TMUX_PANE` environment, as normal when it starts inside tmux.

## Verified behavior

The native `/statusline <command>` path has been used to attach this adapter
while existing Antigravity CLI sessions were running in tmux, without
restarting them. Their native idle signal reached the corresponding panel;
a short real model task also produced the native working signal. The adapter
integration test uses an isolated real tmux server and checks that edits to
the script are picked up by the next invocation. The test does not pretend
to emulate the entire Antigravity harness.

## Mapping

| Native signal | Lamp |
| --- | --- |
| `working`, `tool_use`, `reviewing`, `initializing` | Working |
| `tool_confirmation_pending=true` | Waiting, overriding the activity state |
| `authenticating` | Waiting |
| `idle` | Idle, unless `task_count>0` reports background work |
| `error` | Error |
| Unrecognised or absent state | Connected, state unknown |

Only the few fields needed for status are read. Payloads may include private
paths or account information, but this script never stores or prints them.
It returns success even if `lamp` is unavailable. The status interface does
not guarantee an exit callback: normal or forced process termination may
leave a stale lamp until another reporter or process observer clears it.

Sources: [status line JSON](https://antigravity.google/docs/cli/statusline/),
[native hot attachment command](https://www.antigravity.google/docs/cli/commands/statusline/).
