#!/bin/sh
# Never replace an existing mouse or prefix binding.
set -eu
tmux_bin=${TMUX_BIN:-tmux}

bind_menu() {
    table=$1; key=$2; shift 2
    # The menu remembers the selected pane, including through command-prompt.
    # %%% escapes quotes before tmux parses a name; no shell processes it.
    "$tmux_bin" bind-key -T "$table" "$key" display-menu "$@" \
        -T 'ADON panel controls' \
        'Rename panel' n 'command-prompt -p "Panel name:" '\''set-option -p @pane_name "%%%"'\''' \
        '' \
        'Working (green)' g 'set-option -p @agent_adon_connected 1 ; set-option -p @agent_adon_state working ; set-option -p @agent_adon_detail "" ; set-option -pu @agent_adon_updated' \
        'Waiting (yellow)' y 'set-option -p @agent_adon_connected 1 ; set-option -p @agent_adon_state waiting ; set-option -p @agent_adon_detail "" ; set-option -pu @agent_adon_updated' \
        'Blocked (red)' r 'set-option -p @agent_adon_connected 1 ; set-option -p @agent_adon_state error ; set-option -p @agent_adon_detail "" ; set-option -pu @agent_adon_updated' \
        'Idle (grey)' i 'set-option -p @agent_adon_connected 1 ; set-option -p @agent_adon_state idle ; set-option -p @agent_adon_detail "" ; set-option -pu @agent_adon_updated' \
        'No reported state' u 'set-option -p @agent_adon_connected 0 ; set-option -p @agent_adon_state unknown ; set-option -p @agent_adon_detail "" ; set-option -pu @agent_adon_updated'
}

mouse_available=0
keyboard_available=0
mouse_reason=
mouse_binding=$("$tmux_bin" list-keys -T root MouseDown1Control1 2>/dev/null || :)
case "$mouse_binding" in
    *'ADON panel controls'*)
        if bind_menu root MouseDown1Control1 -t = -x M -y M 2>/dev/null; then
            mouse_available=1
        else
            mouse_reason='could not refresh existing agent-adon mouse binding'
        fi ;;
    '')
        if bind_menu root MouseDown1Control1 -t = -x M -y M 2>/dev/null; then
            mouse_available=1
        else
            mouse_reason='server does not support MouseDown1Control1'
        fi
        ;;
    *) mouse_reason='MouseDown1Control1 is already bound' ;;
esac
"$tmux_bin" set-option -g @agent_adon_controls_available "$mouse_available"

# Offer the same keyboard entry on every server, including those with a
# clickable button. Unrelated existing bindings stay intact; our own are
# refreshed so a menu update takes effect when the plugin is reloaded.
prefix_binding=$("$tmux_bin" list-keys -T prefix a 2>/dev/null || :)
case "$prefix_binding" in
    *'ADON panel controls'*)
        if bind_menu prefix a -x P -y P 2>/dev/null; then
            keyboard_available=1
        else
            printf '%s\n' 'agent-adon: could not refresh existing prefix + a' >&2
        fi ;;
    '')
        if bind_menu prefix a -x P -y P 2>/dev/null; then
            keyboard_available=1
        else
            printf '%s\n' 'agent-adon: could not install prefix + a' >&2
        fi
        ;;
    *)
        printf '%s\n' 'agent-adon: prefix + a is already bound; existing binding preserved' >&2 ;;
esac
"$tmux_bin" set-option -g @agent_adon_keyboard_available "$keyboard_available"
if [ -n "$mouse_reason" ]; then
    if [ "$keyboard_available" -eq 1 ]; then
        printf 'agent-adon: %s; use prefix + a for the panel menu\n' "$mouse_reason" >&2
    else
        printf 'agent-adon: %s; mouse control unavailable\n' "$mouse_reason" >&2
    fi
fi
[ "$mouse_available" -eq 1 ] || [ "$keyboard_available" -eq 1 ]
