#!/usr/bin/env node
/**
 * Minimal npm-compatible registry for the Goose activation-binding canary.
 *
 * Protocol freeze: idea/48_GOOSE_CANARY_PROTOCOL_FREEZE.md
 *
 * Written by hand rather than using verdaccio because this registry IS a measurement
 * instrument, not just plumbing:
 *
 *   - its access log is the ground truth for `resolver_fetch_observed` (idea/48 §3.2),
 *     so the log format has to carry nanosecond timestamps and survive replay;
 *   - repointing the `latest` dist-tag between admission and activation is the core
 *     manipulation of the mutable-selector arm, and it must be atomic and logged;
 *   - zero external dependencies keeps the rig reproducible offline.
 *
 * It serves only what npm/npx actually need: a packument and tarball bytes.
 *
 * Usage:
 *   node test_registry.js --dist <dir> [--port 4873] [--log <path>]
 *
 * Admin (loopback only, not part of the npm protocol):
 *   POST /_admin/repoint/:tag/:version    move a dist-tag
 *   GET  /_admin/state                    current dist-tags
 */

'use strict';

const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

function arg(name, fallback) {
  const i = process.argv.indexOf(`--${name}`);
  return i !== -1 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

const DIST = path.resolve(arg('dist', path.join(__dirname, 'dist')));
const PORT = parseInt(arg('port', '4873'), 10);
const HOST = '127.0.0.1'; // loopback only — never expose this
const LOG = path.resolve(arg('log', path.join(DIST, 'registry_access.jsonl')));

function nowStamp() {
  return {
    wall_ns: (BigInt(Date.now()) * 1000000n).toString(),
    monotonic_ns: process.hrtime.bigint().toString(),
    iso: new Date().toISOString(),
  };
}

const logStream = fs.createWriteStream(LOG, { flags: 'a' });
function accessLog(entry) {
  logStream.write(JSON.stringify({ ...nowStamp(), ...entry }) + '\n');
}

// --- load tarballs from dist/ -------------------------------------------------

function loadPackages() {
  const packages = {};
  for (const file of fs.readdirSync(DIST)) {
    if (!file.endsWith('.tgz')) continue;
    const full = path.join(DIST, file);
    const bytes = fs.readFileSync(full);

    // package.json inside the tarball is authoritative for name/version.
    const m = /^(.*)-(\d+\.\d+\.\d+)\.tgz$/.exec(file);
    if (!m) continue;
    const [, name, version] = m;

    packages[name] = packages[name] || { name, versions: {}, distTags: {} };
    packages[name].versions[version] = {
      name,
      version,
      bin: { [name]: 'canary_server.js' },
      dist: {
        tarball: `http://${HOST}:${PORT}/${name}/-/${file}`,
        shasum: crypto.createHash('sha1').update(bytes).digest('hex'),
        integrity:
          'sha512-' + crypto.createHash('sha512').update(bytes).digest('base64'),
      },
      _file: file,
      _sha256: crypto.createHash('sha256').update(bytes).digest('hex'),
    };
  }

  // Default dist-tag: lowest version. The admission-time artifact must be the
  // one the experiment pins first; repointing is always an explicit action.
  for (const p of Object.values(packages)) {
    const sorted = Object.keys(p.versions).sort();
    p.distTags.latest = sorted[0];
  }
  return packages;
}

const PACKAGES = loadPackages();

if (Object.keys(PACKAGES).length === 0) {
  console.error(`[registry] no .tgz found in ${DIST} — run build_artifacts.sh first`);
  process.exit(2);
}

// --- server -------------------------------------------------------------------

function packument(pkg) {
  const versions = {};
  for (const [v, meta] of Object.entries(pkg.versions)) {
    const { _file, _sha256, ...pub } = meta;
    void _file;
    void _sha256;
    versions[v] = pub;
  }
  return {
    name: pkg.name,
    'dist-tags': pkg.distTags,
    versions,
  };
}

function send(res, code, body, type = 'application/json') {
  const payload = typeof body === 'string' || Buffer.isBuffer(body) ? body : JSON.stringify(body);
  res.writeHead(code, { 'Content-Type': type, 'Content-Length': Buffer.byteLength(payload) });
  res.end(payload);
}

const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);

  // --- admin: dist-tag repoint (the mutable-selector manipulation) ---
  let m = /^\/_admin\/repoint\/([^/]+)\/([^/]+)$/.exec(url);
  if (m && req.method === 'POST') {
    const [, tag, version] = m;
    const pkg = Object.values(PACKAGES)[0];
    if (!pkg.versions[version]) {
      accessLog({ event: 'repoint_rejected', tag, version, reason: 'unknown_version' });
      return send(res, 404, { error: 'unknown version' });
    }
    const previous = pkg.distTags[tag];
    pkg.distTags[tag] = version;
    accessLog({
      event: 'dist_tag_repointed',
      package: pkg.name,
      tag,
      from: previous,
      to: version,
      to_sha256: pkg.versions[version]._sha256,
    });
    return send(res, 200, { package: pkg.name, tag, from: previous, to: version });
  }

  if (url === '/_admin/state') {
    const state = Object.values(PACKAGES).map((p) => ({
      name: p.name,
      distTags: p.distTags,
      versions: Object.fromEntries(
        Object.entries(p.versions).map(([v, meta]) => [v, meta._sha256])
      ),
    }));
    return send(res, 200, state);
  }

  // --- tarball fetch ---
  m = /^\/([^/]+)\/-\/(.+\.tgz)$/.exec(url);
  if (m) {
    const [, name, file] = m;
    const pkg = PACKAGES[name];
    const full = path.join(DIST, file);
    if (!pkg || !fs.existsSync(full)) {
      accessLog({ event: 'tarball_miss', package: name, file });
      return send(res, 404, { error: 'not found' });
    }
    const bytes = fs.readFileSync(full);
    accessLog({
      event: 'tarball_fetch',
      package: name,
      file,
      sha256: crypto.createHash('sha256').update(bytes).digest('hex'),
      user_agent: req.headers['user-agent'] || null,
    });
    return send(res, 200, bytes, 'application/octet-stream');
  }

  // --- packument (metadata) fetch ---
  m = /^\/([^/]+)$/.exec(url);
  if (m) {
    const [, name] = m;
    const pkg = PACKAGES[name];
    if (!pkg) {
      accessLog({ event: 'packument_miss', package: name });
      return send(res, 404, { error: 'not found' });
    }
    accessLog({
      event: 'packument_fetch',
      package: name,
      dist_tags: { ...pkg.distTags },
      user_agent: req.headers['user-agent'] || null,
    });
    return send(res, 200, packument(pkg));
  }

  accessLog({ event: 'unhandled', method: req.method, url });
  send(res, 404, { error: 'not found' });
});

server.listen(PORT, HOST, () => {
  const pkg = Object.values(PACKAGES)[0];
  accessLog({ event: 'registry_start', dist: DIST, port: PORT, dist_tags: pkg.distTags });
  console.log(`[registry] http://${HOST}:${PORT}  dist=${DIST}`);
  console.log(`[registry] access log: ${LOG}`);
  for (const p of Object.values(PACKAGES)) {
    console.log(`[registry] ${p.name}  dist-tags=${JSON.stringify(p.distTags)}`);
    for (const [v, meta] of Object.entries(p.versions)) {
      console.log(`[registry]   ${v}  sha256=${meta._sha256}`);
    }
  }
});
