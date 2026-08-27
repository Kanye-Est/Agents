# 45 — Authorization-Binding Audit：有限抽样框冻结

> 日期：2026-08-11（Asia/Taipei）  
> 协议：`authorization_binding_audit_sampling_frame_v1`  
> 依赖：idea/42 Amendment 1–5；idea/43 §2  
> 状态：**FROZEN BEFORE PRODUCT CODING**  
> 目的：冻结 10 个 primary analysis units 与 3 个有序 reserve units；本文不记录任何 binding 结论。

---

## 1. 抽样问题与边界

本研究做的是**有目的的配置审计（purposive configuration audit）**，不是市场普及率调查。抽样目标是覆盖
不同扩展机制与控制平面，检验 authorization-binding gap 是否在多个独立实现中具有安全实质；不从样本比例
外推产品市场 prevalence。

分析单位严格为：

```text
system × version × platform × configuration profile × extension mechanism
```

同一 core implementation 的多个路径不重复计入“独立系统”数量。

## 2. 冻结前暴露日志与选择独立性

在本清单冻结前，为确认候选是否存在当前维护的第三方扩展机制以及确定版本，研究者打开过下列官方页面：
Claude Code plugin marketplace、Codex skills/MCP、Continue MCP、Cursor MCP、OpenHands MCP、Gemini CLI
extensions、Goose extensions、Cline MCP/CLI plugins、OpenAI Agents SDK MCP、AutoGen MCP Workbench、CrewAI
MCP、LangChain MCP adapters。

这一 inclusion pass 不完全盲：页面搜索摘要或正文中已经看到过少量安装相关文字，例如某些系统出现 confirmation、
approval、auto-approve、pinning 或 install-scope 描述。**冻结前没有填写十字段 binding vector、没有给出
B0–B5/I0–I5 等级、没有运行 canary，也没有因为这些文字把候选加入或移出清单。**

为降低选择偏差，本清单按预先定义的架构配额固定：

- 4 个面向用户的 marketplace / extension / plugin 安装路径；
- 3 个面向用户的 skill / MCP agent runtime 路径；
- 3 个 SDK / framework 的 MCP integration 路径；
- reserve 依次补充 framework、IDE、同一产品的替代扩展路径。

纳入理由只允许使用“接口存在、仍维护、可版本锚定、架构覆盖”信息，不使用授权强弱或疑似漏洞信息。

## 3. Primary analysis units（固定 10 个）

| ID | System / core implementation | Version anchor | Platform | Frozen configuration profile | Extension mechanism | Architecture quota | Inclusion reason | Official anchor |
|---|---|---|---|---|---|---|---|---|
| P01 | Anthropic Claude Code | installed `2.1.217` | Linux x86_64, CLI | GitHub-hosted marketplace added with documented `owner/repo` shorthand and no optional `@ref`; relative-path plugin entry with manifest `version`; user-scope install; other documented defaults | plugin marketplace → plugin installation | marketplace / plugin | current first-party client is locally available; official docs describe this default GitHub path and plugin installation | [Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) |
| P02 | OpenAI Codex CLI | installed `0.146.0` | Linux x86_64, CLI | default interactive profile; user-scoped standalone skill path | standalone skills directory / plugin-distributed skills | skill / runtime | locally available first-party client; official docs define skills as Codex extensions | [Agent Skills](https://developers.openai.com/codex/skills) |
| P03 | Continue | release `v2.0.0-vscode` (2026-06-19) | VS Code on Linux | default agent profile with one user-configured MCP server | MCP server configuration | MCP / runtime | maintained IDE agent with documented local and remote MCP servers | [MCP tools](https://docs.continue.dev/customize/mcp-tools) |
| P04 | OpenHands | release `v1.12.0` (2026-08-07) | Linux, CLI | default CLI profile with one user-added stdio MCP server | CLI MCP server management | MCP / runtime | maintained autonomous-agent runtime with official MCP management docs | [CLI MCP servers](https://docs.openhands.dev/openhands/usage/cli/mcp-servers) |
| P05 | Google Gemini CLI | release `v0.54.4` (2026-08-07) | Linux x86_64, CLI | default interactive profile; user-scope extension installation from a frozen Git source | Gemini CLI extension | marketplace / extension | maintained first-party CLI; extensions package MCP servers, prompts, and commands | [Extensions](https://google-gemini.github.io/gemini-cli/docs/extensions/) |
| P06 | Block/AAIF Goose | release `v1.45.0` (2026-07-29) | Linux x86_64, CLI/Desktop where supported | default profile; one user-enabled community extension | Goose extension | marketplace / extension | maintained agent with a documented MCP extension ecosystem | [Goose documentation](https://block.github.io/goose/) |
| P07 | Cline | release `v4.1.8` (2026-08-11) | Linux x86_64, CLI | default CLI profile; user-scope plugin installation | CLI plugin install from npm/Git/local source | marketplace / plugin | maintained coding agent with a first-party plugin installation command | [CLI reference](https://docs.cline.bot/cli/cli-reference) |
| P08 | OpenAI Agents SDK (Python) | release `v0.20.0` (2026-08-11) | CPython on Linux | minimal documented agent; one stdio MCP server; SDK defaults | MCP server integration | SDK / framework | maintained first-party agent SDK with documented hosted/local MCP integrations | [MCP guide](https://openai.github.io/openai-agents-python/mcp/) |
| P09 | Microsoft AutoGen (Python) | release `python-v0.7.5` (2025-09-30) | CPython on Linux | Core Workbench example profile; one stdio MCP server | `McpWorkbench` | SDK / framework | maintained agent framework with a first-party MCP execution abstraction | [Workbench](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/components/workbench.html) |
| P10 | CrewAI | release `1.15.14` (2026-08-08) | CPython on Linux | minimal documented crew/agent; one MCP server; library defaults | MCP server adapter | SDK / framework | maintained multi-agent framework with a documented MCP integration | [MCP servers as tools](https://docs.crewai.com/v1.15.14/en/mcp/overview) |

Version timestamps are release metadata, not evidence about authorization behavior. P01/P02 use locally observed exact client versions;
the corresponding documentation is recorded with the audit date because documentation can change independently of the client.

## 4. Ordered reserve analysis units（固定 3 个）

Reserves may replace a primary **only** when the primary meets a predeclared exclusion code in idea/43 §2.2. Replacement always
uses the first eligible reserve; a finding, lack of finding, or inconvenient result is not a replacement reason.

| Order | ID | System / core implementation | Version anchor | Platform | Frozen configuration profile | Extension mechanism | Replacement coverage | Official anchor |
|---|---|---|---|---|---|---|---|---|
| 1 | R01 | LangChain MCP Adapters | `langchain-mcp-adapters==0.3.2` (2026-08-06) | CPython on Linux | minimal LangChain/LangGraph agent; one stdio MCP server | MCP adapters | replaces an excluded SDK/framework unit | [Official repository](https://github.com/langchain-ai/langchain-mcp-adapters) |
| 2 | R02 | Cursor | `rolling-docs@2026-08-11`; canary must additionally record client build | Linux x86_64, IDE | default profile; one user-configured MCP server | MCP installation/configuration | replaces an excluded end-user IDE/runtime unit | [MCP documentation](https://docs.cursor.com/context/model-context-protocol) |
| 3 | R03 | Anthropic Claude Code | installed `2.1.217` | Linux x86_64, CLI | default interactive profile; user-scope local stdio MCP server | MCP server configuration | replaces an excluded MCP/runtime unit; same core as P01 and therefore not an additional independent system | [MCP documentation](https://code.claude.com/docs/en/mcp) |

## 5. Non-sample control

HelloAgents / `secskill-lab` is researcher-controlled deployment class D. It is **not** one of the 13 units and does not count
toward independent real-system evidence. It may instantiate a configuration class only after that class is derived from completed
real-system coding.

## 6. Stop and replacement rule

1. Coding stops after all 10 primary units have valid records, after any exclusion replacements are made in reserve order.
2. No new unit may be added because early results appear weak, homogeneous, surprising, or publication-unfriendly.
3. Each exclusion must be logged with one of idea/43 §2.2's fixed exclusion codes and concrete evidence.
4. If all reserves are exhausted, report the shortfall; do not silently broaden the frame.
5. A product with multiple mechanisms still counts once for the “independent core implementation” threshold.

## 7. Pilot selection（不构成编码结果）

P01 Claude Code plugin marketplace is selected for pilot coding because an exact local client is available and its official
documentation exposes enough lifecycle fields to test whether the codebook is operational. It was **not** selected because of an
expected binding grade. Pilot output may amend field definitions or evidence-capture requirements only; it may not introduce
post-hoc policy families, alter the frozen sample, or change the Go/No-Go threshold.

## 8. Pilot-derived source-profile refinement（2026-08-12）

idea/46 发现，同一 extension mechanism 下的 Git/npm/local/pinned/unpinned source 不能共享 identity grade。
因此在不改变 10+3 系统清单、顺序或 Go/No-Go 门的前提下，补冻每个 unit 的
`artifact_source_profile`。这是 codebook operability refinement，不依据 P01 的 binding 结果。

| Unit | Frozen `artifact_source_profile` |
|---|---|
| P01 | unpinned GitHub marketplace checkout + relative plugin path + manifest version |
| P02 | immutable local snapshot copied into the documented user skill directory |
| P03 | deterministic local stdio MCP server from an immutable sandbox snapshot |
| P04 | deterministic local stdio MCP server from an immutable sandbox snapshot |
| P05 | GitHub extension source pinned to a full commit |
| P06 | catalog/community extension referenced by exact published slug/version where the resolver exposes a version; otherwise record the exposed immutable/mutable selector without substituting a different path |
| P07 | npm plugin referenced by exact package version |
| P08 | deterministic local stdio MCP server from an immutable virtual-environment snapshot |
| P09 | deterministic local stdio MCP server from an immutable virtual-environment snapshot |
| P10 | deterministic local stdio MCP server from an immutable virtual-environment snapshot |
| R01 | deterministic local stdio MCP server from an immutable virtual-environment snapshot |
| R02 | deterministic local stdio MCP server from an immutable sandbox snapshot |
| R03 | deterministic local stdio MCP server from an immutable sandbox snapshot |

Local deterministic servers are used to make installation/first-execution traces and positive controls reproducible. Under
idea/43 §7.3, they are labeled `dev_or_sideload` or `official_local_install` as appropriate and support only the boundaries whose
path equivalence is established; they do not stand in for marketplace discovery.

## 9. Pre-bulk-coding clarifications（2026-08-12）

### 9.1 Delegated-acquisition coverage

The frozen manual/configured profiles do not themselves instantiate delegated selection. A bounded, post-pilot exploratory
inventory over the same 10 core implementations is recorded in idea/47 under idea/42 Amendment 6. It does not add sample units
or alter the stop rule. Any documented delegated path found there remains separate from the primary profile unless explicitly
audited later; it cannot retroactively change a manual profile's grade.

### 9.2 Default-behavior claim ceiling

Most frozen profiles are officially supported optional configurations and are therefore expected to be deployment class `B`, not
`A`. The audit may legitimately find zero `A` records. Consequently, the paper must not promise a product-default or industry-
prevalence claim. The Go/No-Go gate allows `A` or `B`, but all conclusions remain configuration-specific.

### 9.3 AutoGen version check

`python-v0.7.5` (2025-09-30) remains the latest non-draft, non-prerelease GitHub release as checked on 2026-08-12. The official
repository is not archived, reports later repository activity, and current stable documentation still exposes `McpWorkbench`.
P09 therefore remains included; the older release date is recorded as a limitation rather than silently treated as deprecation.

### 9.4 Independence accounting

P02 Codex CLI and P08 OpenAI Agents SDK share a vendor but use different core implementations and authorization/extension
codepaths, so they can be reported as codebase-independent under idea/43's definition. Vendor diversity and codebase diversity
will nevertheless be reported separately. For a conservative headline, P02+P08 alone will not be used as the sole “two-system”
support without an additional independent vendor/core implementation.
