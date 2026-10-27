# tmux display integration

Load `plugin/agent-adon.tmux` from the tmux configuration using the actual
installation path:

```tmux
run-shell '/absolute/path/to/tmux-agent-adon/plugin/agent-adon.tmux'
```

Loading it registers format fragments without changing the current border,
theme, pane names, or status values. When `prefix + a` is free, it opens the
menu for the current panel on all supported versions. On servers that support
border mouse controls, `+` also opens the same menu for the clicked panel.
Both bindings are installed only when free; other existing bindings are
preserved, and this plugin's own bindings are refreshed on reload.
If a mouse control cannot be installed, `+` is hidden. Warnings report binding
conflicts and unsupported mouse controls.

Every panel has four lights in fixed order: green (working), yellow (waiting),
red (error), and grey (idle). An attached adapter or a manual state report
powers the lights: each is shown in its own dim colour, and the current state
is bright. An adapter may be connected without a known state; then all lights
are dimly coloured. A disconnected panel has four neutral grey lights. Each
panel reads its own `@agent_adon_connected` and `@agent_adon_state`.

With tmux mouse mode enabled, click `+` beside the four lights to open a
menu for the clicked panel. The menu can rename that panel or manually report
working, waiting, blocked, idle, or no state. Manual status can be superseded
by later reports from a running agent adapter. If mouse mode is off, use tmux
`set -g mouse on` to enable it; the plugin never changes that option itself.
`prefix + a` controls the currently selected panel; the button controls the
clicked panel. Both are available together when their bindings are free and
the server supports mouse controls.

For an existing pane-border format, append a right-aligned indicator, merging
it into your existing format rather than replacing your theme:

```text
#[align=right]#{E:@agent_adon_indicator_format}
```

For example, `#{pane_index}: #{@pane_name}` becomes
`#{pane_index}: #{@pane_name}#[align=right]#{E:@agent_adon_indicator_format}`.
If the current theme already uses right alignment, adapt the fragment to its
layout. A long name or other text in the existing theme can displace the
lights on narrow panels; truncate the left part of that format if needed. The
indicator ends with `#[default]`; restore any theme-specific style afterward.

Alternatively, users without an existing border configuration can opt in to a
ready-made label for one window, replacing `TARGET_WINDOW` with its tmux ID:

```sh
tmux set-option -w -t TARGET_WINDOW pane-border-status top
tmux set-option -w -t TARGET_WINDOW pane-border-format '#{E:@agent_adon_label_format}'
```

The name and optional detail stay on the left; the four lights are on the
right. The label prefers `@pane_name` and falls back to `pane_title`. On narrow
panels, the left side is truncated to leave room for the lights; on extremely
narrow panels there may not be enough columns to show all four.

For terminals without Unicode or colour, replace the indicator with
`#{E:@agent_adon_ascii_indicator_format}` or use
`#{E:@agent_adon_ascii_label_format}` as the ready-made label. It shows
`g y r i`, uppercasing the one active light (for example `G y r i`); unknown
uses all lowercase.

The fragments live in the tmux server and are lost on server restart unless
the plugin is loaded again. A displayed state is only the most recent report;
the fragments cannot detect an Agent crash or stale value.
