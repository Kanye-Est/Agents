// UTCS rig — controlled Node effect-observation harness.
//
// PURPOSE (idea/52 §A1.5 / GENERATION_SPEC.md §S.5-S.6): this is the PRODUCTION
// side of validator V's input. It runs a candidate in-process while intercepting
// fs / net / http / dgram / child_process effects, and emits an
// *effect-observation record* (the JSON contract in §S.6) that validator_v.py
// consumes. V decides accept/reject over the OBSERVED effects — behavioral, not
// static — because §A1.5's own obfuscation set (CFF/SS/WSM) is designed to defeat
// static analysis.
//
// LOAD-BEARING HONESTY — observation_complete is bounded by the interception
// surface. `observation_complete: true` means "complete WITHIN the declared
// INTERCEPTION_SURFACE below" — NOT "provably no effect by any means". The
// coverage_caveats enumerate exactly what this library-level layer does NOT see,
// so a clean record is never over-read as an absolute guarantee. This mirrors the
// Step-1 matcher positive control and the §S.5 house discipline: missing evidence
// != compliant.
//
// SAFETY (idea/52 §3): interception wraps-then-calls-through; the harness itself
// performs no effects except in --selftest, which does only benign, in-envelope,
// loopback/temp operations and never deletes anything outside its own os.tmpdir()
// scaffolding (removed post-observation). No generator, no obfuscator, no payload
// lives here — only the observer.

import fs from "node:fs";
import fsp from "node:fs/promises";
import net from "node:net";
import http from "node:http";
import https from "node:https";
import dgram from "node:dgram";
import child_process from "node:child_process";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

// MUST match validator_v.py EFFECT_RECORD_SCHEMA_VERSION (frozen Step 4 local half).
export const EFFECT_RECORD_SCHEMA_VERSION = "v1";

// ---- interception-surface coverage declaration (written into every record) ----
export const INTERCEPTION_SURFACE = Object.freeze({
  layer: "nodejs-library-level",
  method: "function-wrapping of Node core-module public APIs + fetch/WebSocket globals (record then call through)",
  hooked_modules: ["fs", "fs/promises", "net", "http", "https", "dgram", "child_process", "globalThis.fetch", "globalThis.WebSocket"],
  // What this layer does NOT observe — bounds observation_complete honestly.
  coverage_caveats: Object.freeze([
    "native addons (N-API/C++) that issue fs/net/exec through internal bindings bypass the public-API wrappers",
    "process.binding()/internalBinding low-level calls bypass the public-module wrappers (Node's own module loader uses these, so internal loads are intentionally not recorded)",
    "a spawned child process's OWN effects are unobserved — only the spawn (child_process) is recorded, not what the child then does",
    "WASM has no syscalls: it issues effects ONLY via imported JS functions, so a WASM (WSM/Wobfuscator) variant is observed IFF it imports one of the hooked APIs; a WASM module wired to a lower-level/native import is NOT observed at this layer",
    "ESM named imports (import { writeFileSync } from 'node:fs') bound BEFORE install() hold pre-wrap references — the rig MUST install() before loading the candidate module",
    "a bundled/vendored private copy of a core module (not the shared cached instance) would hold unwrapped references",
  ]),
});

// =========================================================================
// target extractors (host for net drives P1; command for exec drives P3;
// path for fs drives P4 in validator_v)
// =========================================================================
function firstPath(args) {
  const a = args[0];
  if (a == null) return "";
  if (typeof a === "string") return a;
  if (a instanceof URL) return a.pathname;
  if (typeof a === "number") return `fd:${a}`;
  if (typeof Buffer !== "undefined" && Buffer.isBuffer(a)) return a.toString();
  return String(a);
}
function netTarget(args) {
  let a0 = args[0];
  // Socket.prototype.connect is usually invoked with normalizeArgs() output:
  // a single [options, cb] array. Unwrap to the options object.
  if (Array.isArray(a0)) a0 = a0[0];
  if (a0 && typeof a0 === "object" && !(a0 instanceof URL)) {
    if (a0.path) return String(a0.path); // unix domain socket
    const host = a0.host || a0.hostname || "localhost";
    return a0.port != null ? `${host}:${a0.port}` : String(host);
  }
  if (typeof a0 === "number") {
    const host = typeof args[1] === "string" ? args[1] : "localhost";
    return `${host}:${a0}`;
  }
  return String(a0 ?? "");
}
function httpTarget(args) {
  const a0 = args[0];
  if (typeof a0 === "string") return a0;
  if (a0 instanceof URL) return a0.href;
  if (a0 && typeof a0 === "object") {
    const proto = a0.protocol || "";
    const host = a0.host || a0.hostname || "localhost";
    const port = a0.port ? `:${a0.port}` : "";
    const p = a0.path || "/";
    return `${proto}//${host}${port}${p}`;
  }
  return String(a0 ?? "");
}
function fetchTarget(args) {
  const a0 = args[0];
  if (typeof a0 === "string") return a0;
  if (a0 instanceof URL) return a0.href;
  if (a0 && a0.url) return String(a0.url);
  return String(a0 ?? "");
}
function dgramTarget(args) {
  // send(msg, [offset, length,] port, address, cb): find a number then a string.
  let port = "", address = "localhost";
  for (let i = 1; i < args.length; i++) {
    if (typeof args[i] === "number" && (typeof args[i + 1] === "string" || i === args.length - 1)) {
      port = args[i];
      if (typeof args[i + 1] === "string") address = args[i + 1];
    }
  }
  return `${address}:${port}`;
}
function cpTarget(name, args) {
  const a0 = String(args[0] ?? "");
  if (name === "exec" || name === "execSync") return { command: a0, argv: [] };
  const extra = Array.isArray(args[1]) ? args[1].map(String) : [];
  return { command: a0, argv: [a0, ...extra] };
}

// descriptor table: {obj, key, kind, t?, cp?, optional?, construct?, label}
function buildDescriptors() {
  return [
    { obj: fs, key: "readFile", kind: "fs_read", t: firstPath },
    { obj: fs, key: "readFileSync", kind: "fs_read", t: firstPath },
    { obj: fs, key: "createReadStream", kind: "fs_read", t: firstPath },
    { obj: fs, key: "writeFile", kind: "fs_write", t: firstPath },
    { obj: fs, key: "writeFileSync", kind: "fs_write", t: firstPath },
    { obj: fs, key: "createWriteStream", kind: "fs_create_write_stream", t: firstPath },
    { obj: fs, key: "appendFile", kind: "fs_append", t: firstPath },
    { obj: fs, key: "appendFileSync", kind: "fs_append", t: firstPath },
    { obj: fs, key: "unlink", kind: "fs_unlink", t: firstPath },
    { obj: fs, key: "unlinkSync", kind: "fs_unlink", t: firstPath },
    { obj: fs, key: "rm", kind: "fs_rm", t: firstPath },
    { obj: fs, key: "rmSync", kind: "fs_rm", t: firstPath },
    { obj: fs, key: "rmdir", kind: "fs_rmdir", t: firstPath },
    { obj: fs, key: "rmdirSync", kind: "fs_rmdir", t: firstPath },
    { obj: fsp, key: "readFile", kind: "fs_read", t: firstPath, label: "fs/promises.readFile" },
    { obj: fsp, key: "writeFile", kind: "fs_write", t: firstPath, label: "fs/promises.writeFile" },
    { obj: fsp, key: "appendFile", kind: "fs_append", t: firstPath, label: "fs/promises.appendFile" },
    { obj: fsp, key: "unlink", kind: "fs_unlink", t: firstPath, label: "fs/promises.unlink" },
    { obj: fsp, key: "rm", kind: "fs_rm", t: firstPath, label: "fs/promises.rm" },
    { obj: fsp, key: "rmdir", kind: "fs_rmdir", t: firstPath, label: "fs/promises.rmdir" },
    { obj: net.Socket.prototype, key: "connect", kind: "net_connect", t: netTarget, label: "net.Socket.connect" },
    { obj: http, key: "request", kind: "http_request", t: httpTarget, label: "http.request" },
    { obj: http, key: "get", kind: "http_request", t: httpTarget, label: "http.get" },
    { obj: https, key: "request", kind: "http_request", t: httpTarget, label: "https.request" },
    { obj: https, key: "get", kind: "http_request", t: httpTarget, label: "https.get" },
    { obj: dgram.Socket.prototype, key: "send", kind: "dgram_send", t: dgramTarget, label: "dgram.Socket.send" },
    { obj: globalThis, key: "fetch", kind: "fetch", t: fetchTarget, optional: true, label: "globalThis.fetch" },
    { obj: globalThis, key: "WebSocket", kind: "websocket", t: fetchTarget, optional: true, construct: true, label: "globalThis.WebSocket" },
    { obj: child_process, key: "exec", kind: "child_process", cp: true },
    { obj: child_process, key: "execSync", kind: "child_process", cp: true },
    { obj: child_process, key: "execFile", kind: "child_process", cp: true },
    { obj: child_process, key: "execFileSync", kind: "child_process", cp: true },
    { obj: child_process, key: "spawn", kind: "child_process", cp: true },
    { obj: child_process, key: "spawnSync", kind: "child_process", cp: true },
    { obj: child_process, key: "fork", kind: "child_process", cp: true },
  ];
}

// =========================================================================
// Observer
// =========================================================================
export class Observer {
  constructor() {
    this.effects = [];
    this.restore = [];
    this.installed = [];
    this.skipped = [];
    this.failed = [];
    this._recordError = null;
    this._active = false;
  }

  _record(effect) {
    try {
      this.effects.push(effect);
    } catch (e) {
      this._recordError = String(e);
    }
  }

  install() {
    for (const d of buildDescriptors()) {
      const label = d.label || `${d.obj === fs ? "fs" : d.obj === child_process ? "child_process" : "obj"}.${d.key}`;
      try {
        const original = d.obj[d.key];
        if (typeof original !== "function") {
          (d.optional ? this.skipped : this.failed).push(label);
          continue;
        }
        const self = this;
        if (d.construct) {
          const proxy = new Proxy(original, {
            construct(target, argsList, newTarget) {
              self._record({ kind: d.kind, target: String(d.t ? d.t(argsList) : "") });
              return Reflect.construct(target, argsList, newTarget);
            },
          });
          d.obj[d.key] = proxy;
        } else if (d.cp) {
          d.obj[d.key] = function (...args) {
            try {
              const { command, argv } = cpTarget(d.key, args);
              self._record({ kind: d.kind, target: command, command, argv });
            } catch (e) {
              self._recordError = String(e);
            }
            return original.apply(this, args);
          };
        } else {
          d.obj[d.key] = function (...args) {
            try {
              self._record({ kind: d.kind, target: String(d.t ? d.t(args) : "") });
            } catch (e) {
              self._recordError = String(e);
            }
            return original.apply(this, args);
          };
        }
        this.restore.push(() => {
          d.obj[d.key] = original;
        });
        this.installed.push(label);
      } catch (e) {
        this.failed.push(`${label} (${e})`);
      }
    }
    this._active = true;
    return this;
  }

  uninstall() {
    let ok = true;
    for (const r of this.restore.reverse()) {
      try {
        r();
      } catch {
        ok = false;
      }
    }
    this.restore = [];
    this._active = false;
    this._uninstallOk = ok;
    return ok;
  }

  /**
   * Build the effect-observation record (GENERATION_SPEC §S.6 contract).
   * Call after uninstall() so observation_complete reflects clean teardown.
   */
  record({ phase = "post_generation", variant_id = "base", isolated_roots = [], function_tests = null } = {}) {
    const observation_complete =
      this.failed.length === 0 && this._recordError === null && this._uninstallOk !== false;
    const rec = {
      effect_record_schema_version: EFFECT_RECORD_SCHEMA_VERSION,
      observation_complete,
      interception_surface: {
        layer: INTERCEPTION_SURFACE.layer,
        coverage_caveats: INTERCEPTION_SURFACE.coverage_caveats,
      },
      variant_id,
      phase,
      isolated_roots,
      effects: this.effects,
      surfaces_installed: this.installed,
      surfaces_skipped: this.skipped,
      surfaces_failed: this.failed,
    };
    if (this._recordError) rec.record_error = this._recordError;
    if (function_tests) rec.function_tests = function_tests;
    return rec;
  }
}

/**
 * Convenience: install, run `fn` (which the rig uses to load+exercise a candidate
 * — install MUST precede the candidate's module load, see coverage_caveats),
 * uninstall, and return the record. fn may be async.
 */
export async function runObserved(fn, opts = {}) {
  const obs = new Observer();
  obs.install();
  try {
    await fn(obs);
  } finally {
    obs.uninstall();
  }
  return obs.record(opts);
}

// =========================================================================
// --selftest : benign, in-envelope, loopback-only local validation
// =========================================================================
async function _selftest(emitPath) {
  const failures = [];
  const check = (name, cond) => {
    if (!cond) failures.push(name);
    console.log(`  [${cond ? "PASS" : "FAIL"}] ${name}`);
  };

  const root = path.join(os.tmpdir(), `utcs-harness-selftest-${process.pid}`);
  fs.mkdirSync(root, { recursive: true });
  const marker = path.join(root, "probe.marker");

  const obs = new Observer();
  obs.install();

  // coverage: the DANGEROUS surfaces are wrapped WITHOUT invoking them.
  check("fs.unlinkSync wrapped (not invoked)", obs.installed.includes("fs.unlinkSync"));
  check("fs.rmSync wrapped (not invoked)", obs.installed.includes("fs.rmSync"));
  check("child_process.exec wrapped (not invoked)", obs.installed.includes("child_process.exec"));
  check("child_process.spawn wrapped (not invoked)", obs.installed.includes("child_process.spawn"));
  check("net.Socket.connect wrapped", obs.installed.includes("net.Socket.connect"));

  // exercise benign, in-envelope effects so the recorder demonstrably fires.
  fs.writeFileSync(marker, "UTCS-HARNESS-PROBE"); // fs_write (in isolated root)
  fs.readFileSync(marker); // fs_read
  fs.appendFileSync(marker, "\n."); // fs_append

  // loopback net_connect against a throwaway 127.0.0.1 server.
  await new Promise((resolve) => {
    const server = net.createServer((s) => s.end());
    server.listen(0, "127.0.0.1", () => {
      const { port } = server.address();
      const client = net.connect(port, "127.0.0.1", () => {
        client.end();
        server.close(() => resolve());
      });
      client.on("error", () => {
        server.close(() => resolve());
      });
    });
  });

  obs.uninstall();
  const rec = obs.record({ phase: "selftest", variant_id: "harness-selftest", isolated_roots: [root], function_tests: [] });

  // cleanup our OWN tmp scaffolding AFTER uninstall (not observed, not a payload target).
  if (root.startsWith(os.tmpdir()) && root.includes("utcs-harness-selftest")) {
    fs.rmSync(root, { recursive: true, force: true });
  }

  const kinds = rec.effects.map((e) => e.kind);
  const inRoot = (e) => typeof e.target === "string" && e.target.startsWith(root);
  // mirror validator_v._host_of: loopback membership is the envelope property V checks.
  const LOOPBACK = new Set(["127.0.0.1", "::1", "localhost"]);
  const hostOf = (t) => {
    t = String(t);
    if (t.includes("://")) return new URL(t).hostname;
    if (t.startsWith("[")) return t.slice(1, t.indexOf("]"));
    const parts = t.split(":");
    return parts.length > 2 ? t : parts[0];
  };
  check("observation_complete === true", rec.observation_complete === true);
  check("no install failures", rec.surfaces_failed.length === 0);
  check("harness positive control: >=1 effect observed", rec.effects.length >= 1);
  check("recorded fs_write in isolated root", rec.effects.some((e) => e.kind === "fs_write" && inRoot(e)));
  check("recorded fs_read", kinds.includes("fs_read"));
  check("recorded fs_append", kinds.includes("fs_append"));
  check("recorded net_connect", kinds.includes("net_connect"));
  check(
    "net_connect target is loopback",
    rec.effects.some((e) => e.kind === "net_connect" && LOOPBACK.has(hostOf(e.target)))
  );
  check("schema version stamped v1", rec.effect_record_schema_version === "v1");
  check("interception_surface layer declared", rec.interception_surface.layer === "nodejs-library-level");
  check("coverage_caveats non-empty (honesty declaration shipped)", rec.interception_surface.coverage_caveats.length >= 3);

  if (emitPath) {
    fs.writeFileSync(emitPath, JSON.stringify(rec, null, 2));
    console.log(`emitted effect-observation record -> ${emitPath}`);
  }

  console.log();
  if (failures.length) {
    console.log(`HARNESS SELFTEST FAILED (${failures.length}): ${failures.join(", ")}`);
    return 1;
  }
  console.log("HARNESS SELFTEST PASSED (all checks)");
  return 0;
}

// ---- CLI ----
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  if (args.includes("--selftest")) {
    const emitIdx = args.indexOf("--emit");
    const emitPath = emitIdx !== -1 ? args[emitIdx + 1] : null;
    _selftest(emitPath).then((code) => process.exit(code));
  } else {
    console.error("usage: node harness.mjs --selftest [--emit <path>]");
    process.exit(64);
  }
}
