// UTCS tool v1 — stdio MCP server smoke test (local validation, zero-dep).
//
// Proves the transport wrapper (src/server.js) over MCP stdio:
//   1. initialize handshake returns a protocolVersion + serverInfo.name == package name.
//   2. tools/list is BYTE-IDENTICAL to the frozen TOOL_DESCRIPTOR
//      (JSON.stringify(wire) === JSON.stringify(TOOL_DESCRIPTOR)) — the idea/52 §A1.1
//      step-2 anchor: A/v1 and B/v2 advertise the same interface bytes.
//   3. tools/call runs ONE of the 22 frozen cases (test/cases.js) end-to-end through the
//      server and returns exactly that case's expected cleaned output.
//
// Spawns the real server as a child and speaks newline-delimited JSON-RPC to it, so this
// exercises the actual stdio path Goose will use (npx -> bin -> stdio), not an in-process
// shortcut. No dependencies; run: `node test/server_smoke.mjs` (or `npm run smoke`).

import { spawn } from "node:child_process";
import readline from "node:readline";
import { fileURLToPath } from "node:url";
import { TOOL_DESCRIPTOR } from "../src/tool.js";
import { CASES } from "./cases.js";

const SERVER = fileURLToPath(new URL("../src/server.js", import.meta.url));
// The 22-case set includes this whole-document case (has input + expected); run it through
// the live server to confirm the transport preserves the exact mdClean output.
const CASE = CASES.find((c) => c.name === "combined_realistic");

function fail(msg) {
  console.error(`  [FAIL] ${msg}`);
  process.exitCode = 1;
}

async function main() {
  const child = spawn(process.execPath, [SERVER], { stdio: ["pipe", "pipe", "inherit"] });
  const rl = readline.createInterface({ input: child.stdout, crlfDelay: Infinity });

  const pending = new Map(); // id -> resolve
  rl.on("line", (line) => {
    const t = line.trim();
    if (!t) return;
    let msg;
    try { msg = JSON.parse(t); } catch { fail(`server emitted non-JSON line: ${t}`); return; }
    if (msg.id !== undefined && msg.id !== null && pending.has(msg.id)) {
      pending.get(msg.id)(msg);
      pending.delete(msg.id);
    }
  });

  const send = (obj) => child.stdin.write(JSON.stringify(obj) + "\n");
  const request = (id, method, params) =>
    new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error(`timeout waiting for id=${id} (${method})`)), 5000);
      pending.set(id, (m) => { clearTimeout(timer); resolve(m); });
      send({ jsonrpc: "2.0", id, method, ...(params ? { params } : {}) });
    });

  let ok = true;
  const expect = (cond, msg) => { if (!cond) { fail(msg); ok = false; } else console.log(`  [PASS] ${msg}`); };

  try {
    // 1. initialize
    const init = await request(1, "initialize", {
      protocolVersion: "2025-06-18",
      capabilities: {},
      clientInfo: { name: "utcs-smoke", version: "0" },
    });
    expect(typeof init?.result?.protocolVersion === "string", "initialize returns a protocolVersion");
    expect(init?.result?.serverInfo?.name === "utcs-mdclean", "serverInfo.name == utcs-mdclean");

    // initialized notification (no reply expected)
    send({ jsonrpc: "2.0", method: "notifications/initialized" });

    // 2. tools/list — byte-identity with the frozen descriptor
    const list = await request(2, "tools/list");
    const tools = list?.result?.tools;
    expect(Array.isArray(tools) && tools.length === 1, "tools/list returns exactly one tool");
    expect(tools?.[0]?.name === "md_clean", "advertised tool name == md_clean");
    const wire = JSON.stringify(tools?.[0]);
    const frozen = JSON.stringify(TOOL_DESCRIPTOR);
    expect(wire === frozen, "tools/list entry is BYTE-IDENTICAL to frozen TOOL_DESCRIPTOR");
    if (wire !== frozen) {
      console.error(`    wire:   ${wire}`);
      console.error(`    frozen: ${frozen}`);
    }

    // 3. tools/call — one of the 22 frozen cases, end-to-end
    const call = await request(3, "tools/call", { name: "md_clean", arguments: { text: CASE.input } });
    const text = call?.result?.content?.[0]?.text;
    expect(call?.result?.isError !== true, "tools/call did not report isError");
    expect(text === CASE.expected, `tools/call output matches frozen case "${CASE.name}"`);
    if (text !== CASE.expected) {
      console.error(`    got:      ${JSON.stringify(text)}`);
      console.error(`    expected: ${JSON.stringify(CASE.expected)}`);
    }

    // bonus: unknown tool -> isError (not a crash)
    const bad = await request(4, "tools/call", { name: "not_a_tool", arguments: {} });
    expect(bad?.result?.isError === true, "unknown tool name -> result.isError:true");
  } catch (e) {
    fail(String(e?.message || e));
    ok = false;
  } finally {
    child.stdin.end();
    child.kill("SIGTERM");
  }

  console.log(ok && process.exitCode !== 1 ? "SMOKE PASSED" : "SMOKE FAILED");
  if (!ok) process.exitCode = 1;
}

main();
