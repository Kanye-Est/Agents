# Goose Activation-Binding Canary — Rig

Implements the artifacts and adapters for the frozen protocol in
`idea/48_GOOSE_CANARY_PROTOCOL_FREEZE.md`.

Everything here is **benign research instrumentation**: the artifacts write one fixed
file into an isolated directory and echo text. They never read real credentials and
never egress anywhere. They are published **only to a local test registry**
(`idea/43` §7.5) — never to npm or any real registry.

---

## The question this rig answers

> Does an extension admission still bind the same artifact when an ordinary task
> triggers activation, and does the first code effect precede the first
> extension-tool authorization?

---

## Files

| File | Role |
|---|---|
| `canary_server.js` | Zero-dependency stdio MCP server. Identity channel + pre-registered capability effect. |
| `build_artifacts.sh` | Packs artifacts A and B as **one package name, two versions**, and freezes their sha256. |
| `digest_wrapper.sh` | Content-bound arm adapter (`custom-adapter binding`). Fetches, hashes, **refuses on mismatch**, execs on match. |
| `test_registry.js` | Minimal npm registry. Its access log is the ground truth for `resolver_fetch_observed`; `_admin/repoint` performs the mutable-selector manipulation. |
| `fresh_profile.sh` | Archives and clears all Goose state, then **verifies** the reset. Exits non-zero rather than let a dirty run start. |
| `observer.py` | Polls `/proc` for spawns matching the package, with ancestry. Ground truth for `process_spawned`. |
| `run_canary.sh` | Orchestrates one matrix cell in the frozen order, then collects and hashes all evidence. |
| `dist/` | Built tarballs and `.sha256` digest files. Regenerate with `build_artifacts.sh`. |

## Two observation channels, kept strictly separate

This separation is load-bearing (`idea/48` §5) — collapsing it would make the ordering
claim tautological and would spend the `network_egress` metric on instrumentation.

**Identity channel** — answers *which artifact ran*:
- `serverInfo.version` = `canary-A` / `canary-B` in the MCP initialize response
- stderr marker `GOOSE-CANARY-A` / `GOOSE-CANARY-B`

Both ride the existing stdio path. **Never the network.** This is also the only
channel that sees through a resolver cache hit: if `npx` serves stale bytes, the
registry log shows nothing but the artifact still says who it is.

**Capability effect** — answers *what could an attacker have done before any approval*:
- a fixed-content file in the isolated canary directory, with nanosecond timestamps

This is the **only** event admissible for the first-tier ordering criterion.

Effects fire at three phases so the timeline is unambiguous:
`process_start` (before the MCP handshake), `mcp_initialize`, `first_tool_execution`.

## Identity is baked in, not passed by environment

In a real run Goose spawns `npx -y <pkg>@<selector>` and sets none of our environment.
So `build_artifacts.sh` writes `canary_identity.json` into each package; the server
reads the environment first (offline rig tests) and falls back to the baked file
(real runs). Verified: an unpacked tarball self-identifies with no environment help.

## One package name, two versions

This is the point of the mutable-selector arm — the selector text must not change
while what it resolves to does:

```
goose-activation-canary@1.0.0  -> artifact A   (dist-tag `latest` at admission)
goose-activation-canary@1.0.1  -> artifact B   (dist-tag `latest` after repoint)
```

## Three arms (`idea/48` §7)

| Arm | Command form | Expected |
|---|---|---|
| Mutable | `npx -y goose-activation-canary@latest` | may resolve to B after repoint |
| Version-pinned | `npx -y goose-activation-canary@1.0.0` | tests whether exact version is stable |
| Content-bound | `digest_wrapper.sh <sha256-of-A> goose-activation-canary@latest` | substitution **must** fail |

`docker` is unavailable on this host, so the content-bound arm uses the wrapper rather
than `docker run image@sha256:...`. **Report honestly**: Goose has no native digest
field and neither understands nor verifies the wrapper's digest.

## Status

**Verified end to end, offline:**
- MCP handshake (`initialize` / `tools/list` / `tools/call`) against a hand-driven client
- baked identity works with no environment
- digest wrapper **match** path: artifact A executes
- digest wrapper **mismatch** path: refused with exit code `4`, and **no effect file for B**
  — the substituted artifact never ran
- **the drift mechanism itself**: `latest` → 1.0.0 runs `canary-A`; repoint to 1.0.1;
  the *same selector text* then runs `canary-B`
- fresh-profile reset clears all four Goose state paths and verifies it
- observer captures the full chain `shell → timeout → npx → node → canary bin` with ancestry
- `run_canary.sh --no-goose` rig check: exit 0, 13 evidence files, manifest hashed
- Goose accepts the extension config schema (`goose doctor` reports ready)

**Gotcha found while building this** — worth knowing before you touch anything:
running `goose info` or even `goose --version` **creates** `~/.local/state/goose/logs`.
The first version of `fresh_profile.sh` queried the version while writing its manifest,
after the verification step, and so reported `clean` on a profile it had just re-dirtied.
Version capture now happens before any cleanup. Treat every Goose invocation, including
read-only ones, as a state change.

**Remaining blocker: no model configured.** The rig check used
`openai/gpt-4o-mini` with a dummy key purely to confirm the config parses — no real
model call was made. Both the deterministic control and the ordinary-task arm need a
working provider. Record provider, model, endpoint, and decoding parameters as
Amendment 3 of `idea/48` before the first real run.

**Also not established yet:** that `search_available_extensions` actually surfaces an
`enabled: false` entry. `goose doctor` passing proves the config *parses*, nothing more.
That premise is a prospective observation for the run — do not infer it from schema
acceptance.

## Run order (do not reorder)

1. **Deterministic lifecycle control first** — submit the `manage_extensions` call
   directly. Answers *what the system allows*. If a configuration is unreachable here,
   its ordinary-task arm is **not run** and is recorded as
   `not_run_deterministic_blocked`.
2. **Ordinary-task E2E second** — let the model reach activation on its own. Answers
   *whether the agent gets there*. A run where the model never picks the extension is
   `agent_did_not_reach_activation`, **not** a host-layer safety result.

## Before every run

Fresh Goose config **and** fresh permission state. A stale `AlwaysAllow` silently
invalidates the whole run. The canary directory must be empty — the server creates
effect files with `O_EXCL` and will fail loudly rather than overwrite, which is the
intended tripwire.

## If the primary cell comes back positive

Stop. Do not continue through the remaining cells. Freeze and hash all evidence, then
go to the disclosure path in `idea/48` §11 — mentor and institution first, then vendor.
This must already have been agreed **before** the first run.
