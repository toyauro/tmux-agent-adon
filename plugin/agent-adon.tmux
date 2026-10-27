#!/bin/sh
# Register format fragments without changing existing borders or colours.
# Add a mouse binding only if its key is free (or already ours).
set -eu

tmux_bin=${TMUX_BIN:-tmux}
plugin_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

"$plugin_dir/install-menu.sh" || :

"$tmux_bin" set-option -g @agent_adon_button_fragment '#[fg=colour7,range=control|1]+#[norange,default]'
button='#{?@agent_adon_controls_available, #{E:@agent_adon_button_fragment},}'

# Four lights: green/yellow/red/grey. A connected adapter powers the lights
# in dim colours; its current state glows brighter. Disconnected is neutral.
start='#[fg=#1e1e2e,bg=default]#[bg=#1e1e2e]'
finish='#[fg=#1e1e2e,bg=default]#[default]'
green='#{?#{==:#{@agent_adon_connected},1},#{?#{==:#{@agent_adon_state},working},#[fg=#38ff69]#[bold]●#[nobold],#[fg=#285c37]●},#[fg=#585b70]●}'
yellow='#{?#{==:#{@agent_adon_connected},1},#{?#{==:#{@agent_adon_state},waiting},#[fg=#ffe347]#[bold]●#[nobold],#[fg=#725d20]●},#[fg=#585b70]●}'
red='#{?#{==:#{@agent_adon_connected},1},#{?#{==:#{@agent_adon_state},error},#[fg=#ff6b78]#[bold]●#[nobold],#[fg=#773344]●},#[fg=#585b70]●}'
grey='#{?#{==:#{@agent_adon_connected},1},#{?#{==:#{@agent_adon_state},idle},#[fg=#dff5ff]#[bold]●#[nobold],#[fg=#585b70]●},#[fg=#585b70]●}'
spaced="$start$green $yellow $red $grey$finish"
compact="$start$green$yellow$red$grey$finish"
indicator='#{?#{e|<=:#{pane_width},15},#{E:@agent_adon_pill_compact},#{E:@agent_adon_pill_spaced}}'"$button"

# Monochrome/ASCII fallback: uppercase means active. No power = lowercase.
ascii='#{?#{==:#{@agent_adon_connected},1},#{?#{==:#{@agent_adon_state},working},#[fg=#38ff69]G,#[fg=#285c37]g},#[fg=#585b70]g} #{?#{==:#{@agent_adon_connected},1},#{?#{==:#{@agent_adon_state},waiting},#[fg=#ffe347]Y,#[fg=#725d20]y},#[fg=#585b70]y} #{?#{==:#{@agent_adon_connected},1},#{?#{==:#{@agent_adon_state},error},#[fg=#ff6b78]R,#[fg=#773344]r},#[fg=#585b70]r} #{?#{==:#{@agent_adon_connected},1},#{?#{==:#{@agent_adon_state},idle},#[fg=#dff5ff]I,#[fg=#585b70]i},#[fg=#585b70]i}#[default]'"$button"

# A ready-made label for users who don't already have a pane border theme.
# Existing @pane_name is reused rather than overwritten.
# Keep room for four lights, the button, and border padding. On very
# narrow panes hide the name rather than allow it to displace the lights.
left='#{?#{e|<=:#{pane_width},11},,#{=/#{e|-:#{pane_width},11}:#{?@pane_name,#{@pane_name},#{pane_title}}#{?@agent_adon_detail, · #{@agent_adon_detail},}}}'
label="$left"'#[align=right]#{E:@agent_adon_indicator_format}'
ascii_label="$left"'#[align=right]#{E:@agent_adon_ascii_indicator_format}'

"$tmux_bin" set-option -g @agent_adon_pill_spaced "$spaced"
"$tmux_bin" set-option -g @agent_adon_pill_compact "$compact"
"$tmux_bin" set-option -g @agent_adon_indicator_format "$indicator"
"$tmux_bin" set-option -g @agent_adon_ascii_indicator_format "$ascii"
"$tmux_bin" set-option -g @agent_adon_label_format "$label"
"$tmux_bin" set-option -g @agent_adon_ascii_label_format "$ascii_label"
