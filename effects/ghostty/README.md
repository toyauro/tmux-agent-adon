# Optional Ghostty glow

`agent-adon.glsl` adds a static glow around the four bright indicator colours.
It is a **client-side** effect: when Ghostty connects over SSH to an agent on
another device, it renders the lights locally. Other terminals still show the
normal tmux indicator. It never changes the agent state or creates a process.

First test the effect in a separate Ghostty configuration. Add the following
line with the actual absolute path to the repository:

```ini
custom-shader = /path/to/tmux-agent-adon/effects/ghostty/agent-adon.glsl
```

`custom-shader` is repeatable; preserve any shaders you already use. Ghostty
applies them in configuration order. This shader does not use animation time
and does not need an animation loop. If another effect uses animation, do not
disable its loop on this shader's account.

The glow recognises four reserved bright colours: `#38ff69` (working),
`#ffe347` (waiting), `#ff6b78` (error), and `#dff5ff` (idle). It works best
with those exact colours and a true-colour terminal. The shader sees only
rendered pixels, not tmux panel semantics: any other object with matching
colours can glow too; antialiasing, colour management, chained shaders and
fonts can change detection. It makes no guarantee of pixel-perfect isolation.
Test on each client and screen scale. The glow samples nearby pixels and can
affect performance, especially when another shader requests continuous redraw.

If Ghostty becomes unreadable, remove this `custom-shader` line from its
configuration and reload or restart Ghostty. The optional effect needs to be
installed on each viewing client and has not been validated on every Ghostty
version or graphics driver. See [Ghostty's shader documentation](https://ghostty.org/docs/config/reference#custom-shader).
