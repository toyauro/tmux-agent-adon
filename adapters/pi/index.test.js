import { test } from "node:test";
import assert from "node:assert/strict";
import { installPiLamp } from "./index.js";

function harness(pane = "%7") {
  const handlers = new Map();
  const states = [];
  const calls = [];
  let current = "unknown";
  const pi = { on: (event, fn) => handlers.set(event, fn) };
  const invoke = async (args) => {
    calls.push(args);
    if (args[0] === "connect" || args[0] === "disconnect") return "";
    if (args[0] === "get") return current;
    current = args[1];
    states.push({ state: current, args });
  };
  const adapter = installPiLamp(pi, { invoke, pane });
  return { handlers, states, calls, adapter, setCurrent: (value) => { current = value; } };
}

test("events track each Pi work, input prompt and settlement in order", async () => {
  const h = harness();
  h.handlers.get("session_start")({});
  h.handlers.get("agent_start")({});
  h.handlers.get("ui_prompt_start")({});
  h.handlers.get("ui_prompt_end")({});
  h.handlers.get("agent_before_settle")({ outcome: "completed" });
  h.handlers.get("agent_settled")({ aborted: false });
  h.handlers.get("session_shutdown")({ reason: "quit" });
  await h.adapter.flush();
  assert.deepEqual(h.states.map(({ state }) => state), ["idle", "working", "waiting", "working", "idle", "unknown"]);
  assert.equal(h.calls[0][0], "connect");
  assert.equal(h.calls.at(-1)[0], "disconnect");
  assert.ok(h.states.every(({ args }) => args.includes("%7")));
});

test("normal shutdown waits for disconnect even if a status write is queued", async () => {
  const h = harness();
  h.handlers.get("session_start")({});
  await h.handlers.get("session_shutdown")({ reason: "quit" });
  assert.deepEqual(h.calls.map((args) => args[0]), ["connect", "set", "set", "disconnect"]);
  assert.ok(h.calls.every((args) => args.includes("%7")));
});

test("only a settled run-level failure is red; Agent-set red stays red", async () => {
  const h = harness();
  h.handlers.get("agent_start")({});
  h.handlers.get("agent_before_settle")({ outcome: "error" });
  await h.adapter.flush();
  assert.equal(h.states.at(-1).state, "working");
  h.handlers.get("agent_settled")({});
  await h.adapter.flush();
  assert.equal(h.states.at(-1).state, "error");
  h.handlers.get("agent_start")({});
  await h.adapter.flush();
  h.setCurrent("error");
  h.handlers.get("agent_before_settle")({ outcome: "completed" });
  h.handlers.get("agent_settled")({});
  await h.adapter.flush();
  assert.equal(h.states.at(-1).state, "working");
});

test("invalid or absent pane does not install hooks", async () => {
  const h = harness("bad");
  assert.equal(h.handlers.size, 0);
  await h.adapter.flush();
});

test("an unreadable state is not overwritten during settlement", async () => {
  const handlers = new Map();
  const calls = [];
  const adapter = installPiLamp({ on: (event, fn) => handlers.set(event, fn) }, {
    pane: "%7",
    invoke: async (args) => { calls.push(args); return null; },
  });
  handlers.get("agent_before_settle")({ outcome: "completed" });
  handlers.get("agent_settled")({});
  await adapter.flush();
  assert.deepEqual(calls.map((args) => args[0]), ["get"]);
});

test("nested prompts and prompts outside a run restore the correct state", async () => {
  const h = harness();
  h.handlers.get("ui_prompt_start")({});
  h.handlers.get("ui_prompt_start")({});
  h.handlers.get("ui_prompt_end")({});
  h.handlers.get("ui_prompt_end")({});
  await h.adapter.flush();
  assert.deepEqual(h.states.map(({ state }) => state), ["waiting", "waiting", "waiting", "idle"]);
});
