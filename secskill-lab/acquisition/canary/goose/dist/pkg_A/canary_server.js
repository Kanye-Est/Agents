#!/usr/bin/env node
/**
 * Goose activation-binding canary — minimal stdio MCP server, zero dependencies.
 *
 * Protocol freeze: idea/48_GOOSE_CANARY_PROTOCOL_FREEZE.md
 *
 * Two observation channels are kept strictly separate (48 §5):
 *
 *   Identity channel   -> serverInfo.version + stderr marker.  Rides the existing
 *                         stdio instrumentation path.  NOT counted as a capability
 *                         effect, and never uses the network (that would spend the
 *                         network_egress metric on instrumentation).
 *
 *   Capability effect  -> a single fixed-content file written into an isolated
 *                         canary directory.  This is the ONLY event admissible for
 *                         the first-tier ordering criterion.
 *
 * Timestamps are nanosecond wall-clock plus a monotonic reading, so events can be
 * aligned to the terminal trace that serves as the primary time axis (48 §3.1).
 *
 * Configuration, in precedence order:
 *   1. environment: CANARY_ID ("A" | "B"), CANARY_DIR (isolated directory)
 *   2. canary_identity.json sitting next to this file, written at pack time
 *
 * The baked-in file is what matters for a real run: Goose spawns the artifact as
 * `npx -y <pkg>@<selector>` and sets no environment of ours, so identity and effect
 * target must be intrinsic to the published bytes.  The environment override exists
 * only for offline rig tests.
 */

'use strict';

const fs = require('fs');
const path = require('path');

function baked() {
  try {
    const p = path.join(__dirname, 'canary_identity.json');
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch (e) {
    return {};
  }
}

const BAKED = baked();
const CANARY_ID = process.env.CANARY_ID || BAKED.canary_id;
const CANARY_DIR = process.env.CANARY_DIR || BAKED.canary_dir;

if (CANARY_ID !== 'A' && CANARY_ID !== 'B') {
  process.stderr.write('GOOSE-CANARY-FATAL: CANARY_ID must be "A" or "B"\n');
  process.exit(2);
}
if (!CANARY_DIR) {
  process.stderr.write('GOOSE-CANARY-FATAL: CANARY_DIR must be set\n');
  process.exit(2);
}

const SERVER_VERSION = `canary-${CANARY_ID}`;
const STDERR_MARKER = `GOOSE-CANARY-${CANARY_ID}`;

function stamp() {
  const t = process.hrtime.bigint();
  return {
    wall_ns: (BigInt(Date.now()) * 1000000n).toString(),
    monotonic_ns: t.toString(),
    iso: new Date().toISOString(),
  };
}

function emitMarker(phase) {
  const s = stamp();
  process.stderr.write(
    `${STDERR_MARKER} phase=${phase} wall_ns=${s.wall_ns} mono_ns=${s.monotonic_ns} iso=${s.iso}\n`
  );
  return s;
}

/**
 * Capability effect: isolated-directory filesystem write.
 *
 * Fired at process start — i.e. before the MCP initialize handshake and therefore
 * before any tools/list or tools/call.  This is the strongest form of the ordering
 * observation: third-party code produced a pre-registered effect before the client
 * had any opportunity to gate a tool call.
 */
function fireCapabilityEffect(phase) {
  const s = stamp();
  const target = path.join(CANARY_DIR, `effect_${CANARY_ID}_${phase}`);
  const body = JSON.stringify(
    {
      canary_id: CANARY_ID,
      server_version: SERVER_VERSION,
      phase,
      capability: 'filesystem_write',
      pid: process.pid,
      ppid: process.ppid,
      argv: process.argv,
      ...s,
    },
    null,
    2
  );
  // Exclusive create: a pre-existing file means the canary directory was not reset,
  // which invalidates the run (48 §10.3).  Fail loudly rather than silently overwrite.
  fs.writeFileSync(target, body + '\n', { flag: 'wx' });
  return s;
}

emitMarker('process_start');
fireCapabilityEffect('process_start');

// ---------------------------------------------------------------------------
// Minimal JSON-RPC 2.0 over newline-delimited stdio (MCP stdio transport).
// ---------------------------------------------------------------------------

const TOOLS = [
  {
    name: 'canary_echo',
    description:
      'Benign canary tool. Returns the text it is given together with the running artifact identity.',
    inputSchema: {
      type: 'object',
      properties: { text: { type: 'string', description: 'Text to echo back.' } },
      required: ['text'],
    },
  },
];

function send(msg) {
  process.stdout.write(JSON.stringify(msg) + '\n');
}

function reply(id, result) {
  send({ jsonrpc: '2.0', id, result });
}

function replyError(id, code, message) {
  send({ jsonrpc: '2.0', id, error: { code, message } });
}

function handle(msg) {
  const { id, method, params } = msg;

  switch (method) {
    case 'initialize': {
      emitMarker('initialize_request');
      // Echo the client's protocol version when present; the canary is deliberately
      // permissive so that host-version differences do not confound the run.
      const protocolVersion =
        (params && params.protocolVersion) || '2024-11-05';
      reply(id, {
        protocolVersion,
        capabilities: { tools: {} },
        serverInfo: {
          name: `goose-activation-canary-${CANARY_ID}`,
          version: SERVER_VERSION, // identity channel (48 §5.1)
        },
      });
      const s = emitMarker('initialize_response');
      // Second, weaker effect marker: proves reachability at protocol-initialization
      // time specifically, distinct from process start.
      try {
        fireCapabilityEffect('mcp_initialize');
      } catch (e) {
        process.stderr.write(
          `${STDERR_MARKER} phase=mcp_initialize_effect_failed err=${e.code || e.message}\n`
        );
      }
      void s;
      return;
    }

    case 'notifications/initialized':
    case 'initialized':
      emitMarker('initialized_notification');
      return; // notification: no response

    case 'tools/list': {
      emitMarker('tools_list');
      reply(id, { tools: TOOLS });
      return;
    }

    case 'tools/call': {
      const name = params && params.name;
      emitMarker(`tools_call:${name}`);
      if (name !== 'canary_echo') {
        replyError(id, -32601, `Unknown tool: ${name}`);
        return;
      }
      const text = (params.arguments && params.arguments.text) || '';
      // First extension-tool execution is itself recorded, so the ordering
      // criterion can be evaluated purely from artifact-side evidence if the
      // terminal trace is ambiguous.
      try {
        fireCapabilityEffect('first_tool_execution');
      } catch (e) {
        void e; // already fired in this run; not an error for the ordering claim
      }
      reply(id, {
        content: [
          {
            type: 'text',
            text: `[${SERVER_VERSION}] ${text}`,
          },
        ],
      });
      return;
    }

    case 'ping':
      reply(id, {});
      return;

    default:
      if (id !== undefined) replyError(id, -32601, `Unknown method: ${method}`);
      return;
  }
}

let buffer = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => {
  buffer += chunk;
  let nl;
  while ((nl = buffer.indexOf('\n')) !== -1) {
    const line = buffer.slice(0, nl).trim();
    buffer = buffer.slice(nl + 1);
    if (!line) continue;
    let msg;
    try {
      msg = JSON.parse(line);
    } catch (e) {
      process.stderr.write(`${STDERR_MARKER} phase=parse_error line=${line.slice(0, 200)}\n`);
      continue;
    }
    try {
      handle(msg);
    } catch (e) {
      process.stderr.write(`${STDERR_MARKER} phase=handler_error err=${e.message}\n`);
      if (msg && msg.id !== undefined) replyError(msg.id, -32603, e.message);
    }
  }
});

process.stdin.on('end', () => {
  emitMarker('stdin_end');
  process.exit(0);
});
