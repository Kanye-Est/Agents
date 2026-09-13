#!/usr/bin/env node
// UTCS tool v1 — stdio MCP server (transport wrapper over the frozen tool).
//
// idea/52 §A1.1 step 2 (silent-substitution) requires B's advertised interface to be
// BYTE-IDENTICAL to A's. This server does NOT re-declare the tool: it imports the frozen
// TOOL_DESCRIPTOR and callTool from ./tool.js and emits the descriptor object VERBATIM in
// `tools/list`. A/v1 and B/v2 therefore advertise the same bytes — version-string binding,
// not content binding. (goose/config.template.yaml launches this via `npx -y
// utcs-mdclean@<SELECTOR>` from the LOCAL Verdaccio; see the forward item in goose/README.)
//
// Transport: MCP over stdio = newline-delimited JSON-RPC 2.0. One JSON message per line on
// stdin; one JSON message per line on stdout; diagnostics go to stderr only. Implemented
// with Node stdlib alone (node:readline) — ZERO runtime dependencies, matching the tool's
// no-dependency discipline (GENERATION_SPEC §S.1 ecosystem lock: JS/Node/npm).
//
// Handled methods: initialize · notifications/initialized (ignored) · tools/list ·
// tools/call · ping. Unknown method -> JSON-RPC -32601. Parse error -> -32700.
//
// Safety: this is the benign v1 transport. It does NO I/O beyond stdin/stdout and calls
// only the pure mdClean transform. No network, no filesystem, no child processes. The
// payload/obfuscation pipeline (v2) is NOT here and is not shipped in this repo.

import fs from "node:fs";
import readline from "node:readline";
import { TOOL_DESCRIPTOR, callTool } from "./tool.js";

// serverInfo.version tracks the package version (single source of truth).
const PKG = JSON.parse(fs.readFileSync(new URL("../package.json", import.meta.url), "utf8"));

// Fallback only if a (non-conformant) client omits protocolVersion; otherwise we echo the
// client's requested version. Our server is version-agnostic (plain tools capability).
const DEFAULT_PROTOCOL_VERSION = "2024-11-05";

function send(msg) {
  // JSON.stringify never emits a raw newline, so one message == one line (stdio framing).
  process.stdout.write(JSON.stringify(msg) + "\n");
}

function logErr(...args) {
  process.stderr.write(`[utcs-mdclean] ${args.join(" ")}\n`);
}

function isRequest(msg) {
  // A request has an id (number|string). A notification omits id (or id === null).
  return msg != null && typeof msg === "object" &&
    Object.prototype.hasOwnProperty.call(msg, "id") && msg.id !== null && msg.id !== undefined;
}

function handleMessage(msg) {
  if (msg == null || typeof msg !== "object") {
    send({ jsonrpc: "2.0", id: null, error: { code: -32600, message: "Invalid Request" } });
    return;
  }
  const { method, id } = msg;

  // Notifications (no id) never get a reply: initialized, cancelled, progress, etc.
  if (!isRequest(msg)) return;

  try {
    switch (method) {
      case "initialize": {
        const requested = msg.params && typeof msg.params.protocolVersion === "string"
          ? msg.params.protocolVersion : null;
        const protocolVersion = requested || DEFAULT_PROTOCOL_VERSION;
        logErr(`initialize -> protocolVersion=${protocolVersion}`);
        send({
          jsonrpc: "2.0",
          id,
          result: {
            protocolVersion,
            capabilities: { tools: {} },
            serverInfo: { name: PKG.name, version: PKG.version },
          },
        });
        return;
      }

      case "ping":
        send({ jsonrpc: "2.0", id, result: {} });
        return;

      case "tools/list":
        // BYTE-IDENTITY ANCHOR: emit the frozen descriptor object as-is. Do not add,
        // reorder, or wrap fields (test/server_smoke.mjs asserts JSON equality).
        send({ jsonrpc: "2.0", id, result: { tools: [TOOL_DESCRIPTOR] } });
        return;

      case "tools/call": {
        const params = msg.params || {};
        const name = params.name;
        const args = params.arguments || {};
        try {
          const result = callTool(name, args); // { content: [{type:"text", text}] }
          send({ jsonrpc: "2.0", id, result });
        } catch (e) {
          // MCP convention: tool-execution failures are reported inside the result with
          // isError:true, not as a JSON-RPC protocol error.
          send({
            jsonrpc: "2.0",
            id,
            result: { content: [{ type: "text", text: String((e && e.message) || e) }], isError: true },
          });
        }
        return;
      }

      default:
        send({ jsonrpc: "2.0", id, error: { code: -32601, message: `Method not found: ${String(method)}` } });
        return;
    }
  } catch (e) {
    send({ jsonrpc: "2.0", id, error: { code: -32603, message: String((e && e.message) || e) } });
  }
}

function main() {
  const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
  logErr(`stdio MCP server ready (${PKG.name}@${PKG.version})`);

  rl.on("line", (line) => {
    const trimmed = line.trim();
    if (trimmed === "") return; // ignore blank keep-alive lines
    let msg;
    try {
      msg = JSON.parse(trimmed);
    } catch {
      send({ jsonrpc: "2.0", id: null, error: { code: -32700, message: "Parse error" } });
      return;
    }
    // JSON-RPC batches were removed in later MCP revisions; support best-effort anyway.
    if (Array.isArray(msg)) msg.forEach(handleMessage);
    else handleMessage(msg);
  });

  rl.on("close", () => process.exit(0));
  for (const sig of ["SIGINT", "SIGTERM"]) process.on(sig, () => process.exit(0));
}

main();
