import { spawn } from "node:child_process";

// Hooks run without holding up Pi. Serialize writes so a slow earlier hook
// cannot overwrite a later state; lamp failures never stop an agent run.
function runLamp(args) {
  return new Promise((resolve) => {
    const child = spawn(process.env.LAMP_BIN || "lamp", args, {
      shell: false,
      stdio: ["ignore", "pipe", "ignore"],
    });
    let output = "";
    child.stdout.on("data", (chunk) => { output += chunk.toString(); });
    const timer = setTimeout(() => child.kill(), 1000);
    child.on("error", () => { clearTimeout(timer); resolve(null); });
    child.on("close", (code) => { clearTimeout(timer); resolve(code === 0 ? output.trim() : null); });
  });
}

/** Install on a Pi extension API. `invoke` is injectable for isolated tests. */
export function installPiLamp(pi, { invoke = runLamp, pane = process.env.TMUX_PANE } = {}) {
  if (!pane || !/^%\d+$/.test(pane)) return { flush: async () => {} };

  let queue = Promise.resolve();
  let running = false;
  let prompts = 0;
  let outcome;
  const enqueue = (action) => {
    queue = queue.then(action).catch(() => {});
  };
  const set = (state, detail) => invoke(["set", state, "--pane", pane, "--detail", detail]);

  pi.on("session_start", () => {
    running = false;
    prompts = 0;
    // Recognition and activity are separate: a connected agent may have an
    // unknown activity state. The CLI records recognition on this pane.
    enqueue(async () => {
      await invoke(["connect", "--pane", pane]);
      await set("idle", "Pi ready");
    });
  });
  pi.on("agent_start", () => {
    running = true;
    outcome = undefined;
    enqueue(() => set("working", "Pi working"));
  });
  pi.on("ui_prompt_start", () => {
    prompts += 1;
    enqueue(() => set("waiting", "Pi waiting for input"));
  });
  pi.on("ui_prompt_end", () => {
    prompts = Math.max(0, prompts - 1);
    const state = prompts ? "waiting" : running ? "working" : "idle";
    const detail = prompts ? "Pi waiting for input" : running ? "Pi working" : "Pi ready";
    enqueue(() => set(state, detail));
  });
  pi.on("agent_before_settle", (event) => {
    // A failed tool call is not enough. Save only the run-level outcome;
    // Pi may continue, so do not show a final state until agent_settled.
    outcome = event.outcome;
  });
  pi.on("agent_settled", () => {
    running = false;
    const finalOutcome = outcome;
    enqueue(async () => {
      const current = await invoke(["get", "--field", "state", "--pane", pane]);
      // If state could not be read, do not clobber a possible explicit red.
      if (current === null || current === "error") return;
      if (finalOutcome === "error") await set("error", "Pi run failed");
      else await set("idle", "Pi ready");
    });
  });
  pi.on("session_shutdown", () => {
    running = false;
    prompts = 0;
    enqueue(async () => {
      await set("unknown", "Pi session ended");
      await invoke(["disconnect", "--pane", pane]);
    });
    // Shutdown/reload must await the last write: the Pi process may exit as
    // soon as its handlers return. Forced termination cannot run this handler.
    return queue;
  });

  return { flush: () => queue };
}

export default function piLampExtension(pi) {
  installPiLamp(pi);
}
