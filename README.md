# tmux-agent-adon

I built this for my software factory: a fleet of autonomous agents working in
tmux panels across a phone and a Mac. Every panel is a peer and can change its
name and responsibility as the work changes. I want to see where agents are
working, waiting, blocked, or idle at a glance without introducing a central
controller, database, message broker, or a framework that dictates how they
work together.

The same small indicator is useful outside that fleet: **tmux-agent-adon is a
general-purpose status signal for any tmux panel**. Use its CLI directly, or
connect an agent adapter. It is designed to fit into existing themes rather
than replace a user's tmux setup.

Show a name and status for each tmux panel running an agent. Every panel is a
general-purpose workbench: it can be renamed and take on a different role as
the work changes.

```text
 phone use · Checking the phone                 ● ● ● ● +
 review · Waiting for input                     ● ● ● ● +
```

The rounded indicator has four lights on each panel's top-right border, in
green, yellow, red, grey order: working, waiting, blocked, idle. The current
state is bright and the other lights retain their own dim colours. A connected
agent with unknown state shows four dim coloured lights; without a reporter all
four lights are uncoloured and dim.
An ASCII alternative uses
uppercase to identify the lit state when Unicode or colour is unavailable.
A lamp is a status report, not proof
that a task succeeded. It does not route messages or control agents.

Where pane-border mouse controls are supported, click `+` beside a panel's
lights to rename that panel or set its status. Mouse mode must be enabled.
Otherwise, the button is hidden and an available `prefix + a` opens the menu
for the current panel. Existing bindings are never replaced.

The standard indicator works with ordinary terminal text. For a soft glow like
an instrument panel, Ghostty users can opt into the experimental static
[glow shader](effects/ghostty/README.md). It runs on the viewing client, so it
also works when viewing a remote tmux session over SSH. Other terminals keep
the normal indicator. The shader matches pixels by colour, so unrelated text
using a matching colour may also glow.

## Install

Clone the repository, add `bin/` to your `PATH`, and load the tmux plugin.
For example, with a clone in `~/.local/share/tmux-agent-adon`:

```sh
git clone https://github.com/toyauro/tmux-agent-adon.git ~/.local/share/tmux-agent-adon
export PATH="$HOME/.local/share/tmux-agent-adon/bin:$PATH"
tmux run-shell "$HOME/.local/share/tmux-agent-adon/agent-adon.tmux"
```

Loading the plugin registers reusable format fragments and, if available, a
mouse binding for the `+` control. It **does not change existing pane
borders or names**, and it never replaces an existing control binding. Insert
`#{E:@agent_adon_indicator_format}` into your existing `pane-border-format`, or
enable the bundled complete label on a chosen window as described in
[examples/README.md](examples/README.md). Load the plugin again after the tmux
server restarts. A TPM-compatible entrypoint is included at the repository root.

The shell CLI requires `tmux`, POSIX `sh`, and common Unix utilities. The Pi
adapter additionally needs Pi and Node.js; the optional hook bridge for Claude
Code, Codex and Antigravity needs Python 3. tmux 3.8 and 3.6a have been tested;
3.6a uses the keyboard menu described above.

## Report status

From a shell inside a tmux panel:

```sh
lamp set working --name 'phone use' --detail 'Checking the phone'
lamp set waiting --detail 'Waiting for review'
lamp set error --detail 'Unable to proceed'
lamp set idle --name dev
lamp set unknown --detail 'Agent disconnected'
lamp connect
lamp disconnect
lamp get --field state
```

The current `$TMUX_PANE` is used by default. Specify `--pane %ID` to select a
particular pane on the current tmux server. The ID is server-local, not a
cross-device address; query the intended server over SSH. A name is for people
to read and can be changed or duplicated. When `--detail` is omitted, the old
detail is cleared. Name and detail are limited to 512 bytes, are single-line,
and currently reject `#` to prevent tmux format/style injection.

`lamp set --name` updates the conventional `@pane_name` pane option, which can
also be maintained by an existing tmux configuration. The lamp-specific state,
detail, and timestamp are stored in pane-local `@agent_adon_*` options.
`connect` records a reporter and `disconnect` clears it; setting a known state
also records a report, including a manual report. This is not a process
liveness check: a crash can leave a stale report.

## Optional agent integration

All adapters are opt-in; they do not install hooks, change user configuration,
or start background servers. A running agent must load the relevant adapter.

- **Pi**: put `lamp` in the Pi process's `PATH` or set `LAMP_BIN` to its
  absolute path, then start Pi with `-e /path/to/tmux-agent-adon/adapters/pi`.
  Agent start, blocking UI prompts and final settlement drive the light. An
  explicitly reported error is kept until the next run. The Pi adapter needs
  a version that provides the corresponding extension events.
- **Claude Code, Codex and Antigravity CLI**: see
  [the opt-in hook examples and limitations](adapters/hooks/README.md).
  They provide conservative partial integration; live event ordering and
  version support have not yet been verified for these three agents.
- Any agent or person can invoke `lamp` directly. Additional adapters only need
  to translate their own supported events into the same CLI calls.

Hooks cannot observe every kind of wait or business failure. A tool error is
not automatically a blocked task; ending an agent turn is not proof of success.
Forced termination may leave the last reported lamp visible. tmux does not
persist the state after its server exits. There is no heartbeat or automatic
staleness detection in this version; use the reported timestamp to investigate
and use `unknown` when the status cannot be confirmed.

## Verify

```sh
python3 -m unittest discover -s tests -v
python3 -m unittest -v adapters.hooks.test_lamp_hook
node --test adapters/pi/*.test.js
```

The integration tests create their own tmux server and clean it up. No existing
panels or user agent configuration are modified.

MIT licensed; see [LICENSE](LICENSE).
