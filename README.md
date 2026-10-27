<div align="center">

# tmux-agent-adon

**A little signal light for every agent workbench.**

[English](README.md) · [简体中文](README.zh-CN.md) · [Quick start](#quick-start) · [Agent adapters](#agent-adapters)

![MIT license](https://img.shields.io/badge/license-MIT-blue.svg)
![tmux](https://img.shields.io/badge/tmux-3.6a%20%7C%203.8-1BB91F.svg)
![No daemon](https://img.shields.io/badge/runtime-no%20daemon-7c6fdb.svg)

</div>

![Illustration of four tmux agent panels with individual status lights](assets/fleet-demo.svg)

## Why I built this

I am building a software factory: a fleet of autonomous agents working across
a phone and a Mac. Each tmux panel is a peer and can take a different name or
responsibility as its context changes. I wanted to see which workbenches were
working, waiting, blocked, or idle at a glance.

**tmux-agent-adon is the signal light for that fleet, and a small, general-purpose
component for any tmux panel.** It keeps state in tmux and lets agents use
ordinary commands. There is no central controller, database, message broker, or
required background daemon. Agents remain free to choose how they work together.

## The lights

Each panel has the same four lights, displayed at the top right:

| Light | Panel status |
| :---: | --- |
| 🟢 | Working |
| 🟡 | Waiting for input, another agent, or an external condition |
| 🔴 | Blocked or reporting an error |
| ⚪ | Idle |

With an agent adapter or a manual status report, the four lights have dim
colours and the current state is bright. A connected reporter with an unknown
state leaves all four dimly coloured; a panel with no reporter shows four
neutral dim lights. The lights report panel status, not task success.

Names are flexible: a panel can be `phone use` for one task and `dev` for the
next. An available `prefix + a` opens the menu for the current panel; on
servers with mouse controls, clicking `+` opens the same menu for that panel.
Existing unrelated bindings are not overwritten.

## Quick start

Requirements: tmux, POSIX `sh`, and common Unix utilities. Tested with tmux
3.6a and 3.8. Unicode/Powerline glyph support is recommended; an ASCII format
is available in the [display guide](examples/README.md).

**1. Clone and load the plugin.** Run this inside the tmux server you want to use:

```sh
git clone https://github.com/toyauro/tmux-agent-adon.git ~/.local/share/tmux-agent-adon
export PATH="$HOME/.local/share/tmux-agent-adon/bin:$PATH"
tmux run-shell "$HOME/.local/share/tmux-agent-adon/agent-adon.tmux"
```

Add the `PATH` entry to your shell configuration if you want it in future
shells. Load the plugin again after restarting the tmux server; the repository
also includes a TPM-compatible entrypoint.

**2. Show the lights.** To try the bundled label in the current window:

```sh
tmux set-option -w pane-border-status top
tmux set-option -w pane-border-format '#{E:@agent_adon_label_format}'
```

This changes that window's border format. If you already use a tmux theme,
keep it and merge `#[align=right]#{E:@agent_adon_indicator_format}` into your
existing format instead. See the [display guide](examples/README.md) for
theme integration, mouse controls, and the ASCII alternative.

**3. Set your panel's status.**

```sh
lamp set working --name 'phone use' --detail 'Checking the phone'
lamp set waiting --detail 'Waiting for review'
lamp set error --detail 'Unable to proceed'
lamp set idle
lamp disconnect                     # Return to neutral, no-reporter lights
```

`lamp` targets the current `$TMUX_PANE`; `--pane %ID` selects a panel on the
same tmux server. `lamp get --field state` reads the current state. A name can
be changed or duplicated and is not a network address. `lamp set unknown`
clears the known state but does not disconnect an existing reporter.

## Agent adapters

Adapters are optional. They translate available agent events into the same
panel-local state; they do not change how agents plan or use tools.

| Agent | Integration | Validation |
| --- | --- | --- |
| **Pi** | `pi -e /path/to/tmux-agent-adon/adapters/pi` | Loaded on an Android phone; idle → working → idle verified with a real task. |
| **Claude Code** | [Opt-in hooks](adapters/hooks/README.md) | A running isolated session reloaded hooks and reported working → idle. |
| **Codex** | [Hooks and hot-loading](adapters/codex/README.md) | Hook hot-loading tested in an isolated TUI; shared-daemon panel binding is still experimental. |
| **Antigravity CLI** | [Native status-line adapter](adapters/agy/README.md) | Running panels on macOS reported idle → working → idle without restarting. |
| **Other agents** | Call `lamp` from a shell | No agent-specific integration required. |

For Pi, ensure `lamp` is on its `PATH`, or set `LAMP_BIN` to the executable's
absolute path before starting Pi. Hook-based adapters also require Python 3 and
must be configured and trusted according to the agent's own rules.

## Optional glow

The standard indicator uses terminal text. Ghostty users can try the optional
[static glow shader](effects/ghostty/README.md) for a softer instrument-panel
look. It renders on the viewing client, including when viewing a remote phone
over SSH. This effect is experimental: similar colours elsewhere in the
terminal may glow, and it requires validation with your terminal and theme.

## Boundaries

- A state is a report, not a liveness guarantee. A forced exit may leave a
  stale light; there is no heartbeat or automatic stale-state detection.
- tmux server restarts clear its pane-local state. A reporter must reconnect.
- An individual tool failure does not necessarily mean the agent is blocked;
  turn completion does not prove the underlying task succeeded.
- This project displays signals. It does not route messages or coordinate
  agent tasks.

## Development

```sh
python3 -m unittest discover -s tests -v
python3 -m unittest -v adapters.hooks.test_lamp_hook
node --test adapters/pi/*.test.js
```

The tmux tests use isolated servers. Contributions and new agent adapters are
welcome. Licensed under the [MIT License](LICENSE).
