# Codex hooks: load and update without restarting

Codex can connect a running interactive session to the optional hook bridge.
The tested path is **reviewing and trusting new hook declarations in `/hooks`**.
Creating `hooks.json` on disk by itself is not proof that an existing session
has loaded those hooks.

## Load the bridge into a running session

1. Merge the entries from [codex.example.json](../hooks/codex.example.json) into
   the appropriate Codex hooks file, preserving existing entries. For an agent
   already running, use absolute command paths rather than relying on newly
   exported environment variables. For example, a `UserPromptSubmit` handler
   can call:

   ```text
   python3 /absolute/path/to/tmux-agent-adon/adapters/hooks/tmux-hook.py codex UserPromptSubmit
   ```

   Repeat that command shape with the event for each configured handler. The
   dispatcher verifies the owning terminal or a previously established
   session binding before invoking the bridge. The bridge finds this
   checkout's `bin/lamp` by default; an existing `LAMP_BIN` environment
   variable can override it. See the
   [hook configuration and coverage guide](../hooks/README.md).

2. Check that the target panel is displaying the actual Codex input, rather
   than a tmux copy/view mode. From another shell, an explicit panel ID can be
   checked with:

   ```sh
   tmux display-message -p -t %ID 'in_mode=#{pane_in_mode} mode=#{pane_mode}'
   ```

   Replace `%ID` with the intended panel ID on the intended tmux server. If
   `in_mode=1`, leave copy/view mode yourself before proceeding. **Do not send
   `/hooks` or Enter into copy/view mode**: Enter may be bound to a different
   tmux action, such as opening the URL under the cursor. Also check that the
   Codex input is empty and that the agent is not working on another task.

3. In the Codex prompt, type `/hooks` and submit it. Review the new entries and
   trust only the declarations you have checked. In the tested CLI, `t` trusts
   all displayed entries. This is the normal Codex trust flow, not a trust
   bypass.

4. Close the hooks browser and submit a small test task. Confirm the panel
   receives the real event. The presence of a hooks file or an active entry in
   a menu alone is insufficient verification.

## Bind a shared-daemon session

Some Codex hooks are executed by a shared background process without the
interactive terminal's TTY. The dispatcher deliberately refuses to guess the
panel in that case. An existing session is **not automatically discovered**:
first read its session UUID from `/status` in the actual target panel, then,
from a shell connected to the intended tmux server, bind that exact panel:

```sh
python3 /absolute/path/to/tmux-agent-adon/adapters/codex/bind.py \
  --pane %PANE_ID --session-id SESSION_UUID_FROM_THAT_PANEL
```

Substitute the exact pane ID and UUID. `bind.py` verifies the pane, a unique
foreground Codex process, its TTY, and process start time. It **cannot prove**
that a manually supplied session UUID belongs to that process. The person
binding it must obtain the UUID from `/status` in the same panel; do not reuse
an ID based on a matching working directory or pane name. The dispatcher
rechecks the process identity and session ID before forwarding later events.
Restarting or replacing the process invalidates the binding. Verify the next
real event before relying on the display.

If automating a disposable test panel, send the text and Enter as separate
steps with enough time for the TUI to process the text. Sending them back to
back can be treated as a paste and leave the text unsubmitted. Do not use
automation to replace a user's unsubmitted input.

## What updates are hot

Once a fixed hook command is loaded and trusted, it launches the bridge script
for every corresponding event. Editing that script or the `lamp` executable
therefore takes effect on the next event without restarting Codex or reviewing
an unchanged declaration again.

Changing the hook declaration itself is different: Codex trusts the exact
current definition. A new or changed declaration requires review. If no new
lifecycle event has occurred, hot-loading does not by itself prove a current
working, waiting, or idle state.

## Validation and limits

Codex CLI **0.164.0** was tested in an isolated real TUI:

- The process started before its hooks file existed.
- The hooks file was added while the process was running.
- `/hooks` review and trust loaded the declarations without a restart.
- The next real turn emitted `SessionStart`, `UserPromptSubmit`, and `Stop`.
- Updating the script in place produced the new script version's events on the
  next turn, without reopening `/hooks` or restarting the process.

The test used normal hook trust and did not bypass it. Its private temporary
configuration and authentication copy were cleaned up afterward. This result
establishes the tested interactive workflow; it does not establish automatic
file watching by every Codex client or refresh behavior for every app-server
thread.

The current bridge maps Codex `Stop` to `idle` and `Interrupt` to `idle` as
activity hints. `Stop` is a pre-continuation hook: another hook may request
more work, so the displayed idle state may be temporary and does **not** prove
final idle or task success. A later prompt or tool event can report working
again. Codex's app-server exposes runtime status, but this bridge does not
subscribe to that status or automatically map an existing thread to a panel.

A hook environment can also belong to a shared background process. Integrations
must verify panel ownership before writing a lamp; an unverified pane ID must
not be used to update an unrelated panel.

Official reference: [Codex lifecycle hooks](https://learn.chatgpt.com/docs/hooks).
