# UTCS — Goose pre-provision (Step 4 local half)

> **STATUS: DRAFT / pre-provision.** `run = 0`. This directory pins the *shape* of
> the Goose wiring so the VM half can enable it deterministically once the platform
> (S1) is recovered. Nothing here launches a model or an extension.
> Source of truth for scope/safety: `idea/52_DIRECTION1_REDTEAM_PREREGISTRATION.md`
> §6.3 (authorization) + §3 (safety envelope).

## What this is

`config.template.yaml` mirrors the real Goose 1.45 `config.yaml` format (the same
top-level `GOOSE_*` / `OPENAI_*` keys + an `extensions:` map of `type: stdio`
entries). It is a **repo template** — it does **not** overwrite the live
`~/.config/goose/config.yaml`.

It registers tool **A** (`utcs-mdclean`, tool name `md_clean`) as the phase-1
trust-establishment extension (`BASELINE_TASK_DRAFT.md`).

## Local half (pinned NOW) vs VM half (deferred)

| Item | Where | State |
|---|---|---|
| Config **shape** (keys, extension entry, registry pointer) | local | **pinned** (this template) |
| Mutable `@<SELECTOR>` string (the phase-2 repointing arm) | local shape / VM value | shape pinned; **exact string frozen at rig** |
| Backend model + `OPENAI_HOST` concrete values | VM | **deferred** (placeholders) |
| `enabled: true` + actual extension launch | VM | **deferred** (OFF here) |
| `utcs-mdclean` **MCP stdio-server bin** (see below) | rig integration | **forward item** |
| Publishing `utcs-mdclean` to local Verdaccio `127.0.0.1:4873` | VM (S1) | **deferred** |

## Forward item — the stdio MCP-server bin

A Goose `type: stdio` extension speaks MCP over stdio. `tool_v1/` currently ships
the **function** (`mdClean`), the frozen `TOOL_DESCRIPTOR`, and `callTool()` — but
**not** an MCP-server entry point (`bin`). Wiring `callTool`/`TOOL_DESCRIPTOR` into
a stdio MCP server is a **rig-integration item** (VM half: "E2E rig validation"),
deliberately not half-built here without the rig to validate it against Goose.
When added, it must keep the **byte-identical `tools/list`** anchor (A/v1 and B/v2
advertise the same descriptor — version-string binding, not content binding).

## Safety (inherited, idea/52 §3)

- **Loopback only.** `OPENAI_HOST` is `127.0.0.1`; the extension registry is the
  **local Verdaccio** `http://127.0.0.1:4873`. **No public npm** on the experiment
  path. No public egress.
- **Extension is `enabled: false`** here; it is flipped on **only** under an
  authorized §6.3 run, VM-side. Authorized ≠ started (`run = 0`).
- The baseline phase runs **benign content only** — no synthetic credentials, no
  network effects. The `sk-FAKE` read / marker write / loopback POST / canary edit
  effects belong to phase-3's **v2**, not to this trust-establishment config.
