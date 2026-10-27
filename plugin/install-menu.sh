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

mouse_binding=$("$tmux_bin" list-keys -T root MouseDown1Control1 2>/dev/null || :)
case "$mouse_binding" in
    *'ADON panel controls'*)
        bind_menu root MouseDown1Control1 -t = -x M -y M
        "$tmux_bin" set-option -g @agent_adon_controls_available 1
        exit 0 ;;
    '')
        if bind_menu root MouseDown1Control1 -t = -x M -y M 2>/dev/null; then
            "$tmux_bin" set-option -g @agent_adon_controls_available 1
            exit 0
        fi
        reason='server does not support MouseDown1Control1' ;;
    *) reason='MouseDown1Control1 is already bound' ;;
esac

# Older servers cannot hit-test a control range on a pane border. Give them a
# keyboard menu for the current pane instead of a misleading fake button.
"$tmux_bin" set-option -g @agent_adon_controls_available 0
prefix_binding=$("$tmux_bin" list-keys -T prefix a 2>/dev/null || :)
case "$prefix_binding" in
    *'ADON panel controls'*)
        bind_menu prefix a -x P -y P
        printf 'agent-adon: %s; use prefix + a for the panel menu\n' "$reason" >&2
        exit 0 ;;
    '')
        if bind_menu prefix a -x P -y P 2>/dev/null; then
            printf 'agent-adon: %s; use prefix + a for the panel menu\n' "$reason" >&2
            exit 0
        fi
        printf 'agent-adon: %s; could not install prefix + a\n' "$reason" >&2
        exit 1 ;;
    *)
        printf 'agent-adon: %s; prefix + a is also already bound, so the menu was not installed\n' "$reason" >&2
        exit 1 ;;
esac
