# 47 — Delegated-Acquisition Capability Pass（10 Core Implementations）

> 日期：2026-08-12  
> 依赖：idea/42 Amendment 6；idea/45 primary list  
> 状态：**POST-PILOT EXPLORATORY INVENTORY — NOT PREREGISTERED, NOT A BINDING AUDIT**  
> 目的：回答现有抽样是否覆盖真实的 delegated selection 路径，并决定 Htrans 的合法表述上限。

---

## 1. 诚信与范围

本 pass 是在 P01 pilot 完成后因 review 发现设计覆盖缺口而增加。纳入/版本核实时已看过部分安装文档；在
route grades 正式写入 idea/42 Amendment 6 前，又已看到 Claude Code relevance、Goose Extension Manager
与 Cline MCP 的部分结果。因此本文只能称为 **post-pilot exploratory capability inventory**。

本文不改变 idea/45 的 10+3 sampling frame，不给 binding vector 打分，不运行 canary，也不从公开文档
缺失推断产品不具备某能力。

## 2. 编码问题与 route grades

对每个 primary core implementation 记录：

```text
trigger → discovery → candidate selection → install/enable trigger
        → first-execution reachability → candidate-specific approval evidence
        → external/third-party provenance evidence
```

Route grades 使用 `R3/R2/R1/R0/RU`，定义见 idea/42 A6.2。它们不是安全等级：`R3` 不代表无批准，`R0`
也不代表产品安全，只描述文档中选择权从谁开始转移。

## 3. Results

| ID | System / version | Grade | Documented route | Install / activation boundary | Approval evidence | Evidence |
|---|---|---:|---|---|---|---|
| P01 | Claude Code `2.1.217` | `R2` | Admin-allowlisted marketplace metadata can match cwd/files/commands from an ordinary session and surface a specific plugin suggestion. The selector is product-side signal matching, not proof of model reasoning. | Suggestion only; the documented path does not auto-install. | Official docs explicitly retain user confirmation. | [Plugin relevance](https://code.claude.com/docs/en/plugin-relevance), snapshot 2026-08-12 |
| P02 | Codex CLI `0.146.0` | `R0` (`selection=RU`) | Codex can implicitly choose an **already installed** skill. Installation is performed through the explicitly invoked skill installer; docs allow prompting it to download from another repository but do not establish ordinary-task candidate discovery/selection. | Agent-mediated installer exists, but candidate/source selection without acquisition intent is undocumented. | Not evaluated in this pass. | [OpenAI Codex skills](https://developers.openai.com/codex/skills), snapshot 2026-08-12 |
| P03 | Continue `v2.0.0-vscode` | `R0` | User/developer adds an MCP configuration, including a concrete `uses` slug; Agent mode later chooses among exposed tools. | Server acquisition/configuration precedes the ordinary task. | Per-tool Agent-mode approval exists but is not installation authorization. | [Continue MCP configuration](https://docs.continue.dev/reference/continue-mcp), snapshot 2026-08-12 |
| P04 | OpenHands `v1.12.0` | `R0` | User manages and enables a named MCP server through CLI/configuration; the agent automatically receives tools from enabled servers. | No documented ordinary-task discovery/installation path found in the inspected official page. | `RU` for acquisition approval beyond the user-managed setup. | [OpenHands MCP servers](https://docs.openhands.dev/openhands/usage/cli/mcp-servers), snapshot 2026-08-12 |
| P05 | Gemini CLI `v0.54.4` | `R0` | User runs `gemini extensions install` with a GitHub URL or local path. Management commands are explicitly outside interactive agent mode. | Candidate/source is supplied before installation; restart activates it. | Install has a confirmation that can be skipped with an explicit consent flag. | [Gemini CLI extension reference](https://github.com/google-gemini/gemini-cli/blob/main/docs/extensions/reference.md), snapshot 2026-08-12 |
| P06 | Goose `v1.45.0` | `R3-activation` | After the user enables the Extension Manager, an ordinary task can make Goose recognize a missing capability, search available extensions, select one, and enable it during the session. | Official text proves dynamic discovery/enablement and reachability to an active extension; whether arbitrary third-party code is newly downloaded at that moment is undocumented. | Candidate-specific confirmation behavior is undocumented in the inspected page and must be canary/source audited. | [Goose Extension Manager at v1.45.0](https://github.com/aaif-goose/goose/blob/v1.45.0/documentation/docs/mcp/extension-manager-mcp.md), snapshot 2026-08-12 |
| P07 | Cline `v4.1.8` | `R1` | When the user explicitly asks Cline to find or create an MCP server, Cline can choose/create a candidate, clone an existing repository, build it, and integrate it. | Agent advances acquisition, but the documented trigger is an acquisition request rather than an unrelated ordinary task. | File/terminal actions normally use Cline's tool approval policy; exact candidate-binding remains for taxonomy/canary. | [Cline MCP overview](https://docs.cline.bot/mcp/mcp-overview), snapshot 2026-08-12 |
| P08 | OpenAI Agents SDK `v0.20.0` | `R0` | Developer supplies a server URL/object in `HostedMCPTool` or `mcp_servers`; the model can lazily load/select tools from that preconfigured server. | Tool search is scoped to configured/deferred tools and is not external server/artifact acquisition. | SDK exposes configurable per-tool approval, not an installation grant. | [OpenAI Agents SDK MCP](https://openai.github.io/openai-agents-python/mcp/), snapshot 2026-08-12 |
| P09 | AutoGen `python-v0.7.5` | `R0` | Developer installs/configures MCP dependencies and supplies server parameters or a workbench; the model chooses from returned tool adapters. | Artifact/server selection occurs in application code before the task. | No agent-initiated acquisition approval path documented in the inspected page. | [AutoGen MCP Workbench](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/components/workbench.html), snapshot 2026-08-12 |
| P10 | CrewAI `1.15.14` | `R0` | Developer places server URLs/slugs/stdio parameters in the agent's `mcps` configuration; server tools then become available automatically. | Automatic tool discovery occurs only after developer-specified MCP configuration. | No delegated server acquisition authorization documented in the inspected page. | [CrewAI MCP integration](https://docs.crewai.com/v1.15.14/en/mcp/overview), snapshot 2026-08-12 |

Summary:

```text
R3 ordinary-task delegated activation:   1  (Goose; extension provenance and download semantics unresolved)
R2 ordinary-task recommendation:         1  (Claude Code)
R1 explicit-acquisition delegation:      1  (Cline)
R0 candidate/developer specified:        7
RU as whole-route grade:                 0
```

These are counts inside a purposive 10-core inventory, **not prevalence estimates**.

## 4. What this establishes — and what it does not

### Established at document/source level

1. Delegated selection is not purely hypothetical: Goose documents an officially supported optional Extension Manager path in
   which an ordinary task drives extension discovery and activation. The inspected page does not yet prove that the selected
   extension is newly acquired third-party code.
2. Adjacent but weaker forms also exist: Claude Code performs task/session-conditioned recommendations, and Cline supports
   agent-mediated acquisition after an explicit request to find/add a capability.
3. Most inspected framework/SDK profiles document selection among already configured tools, not acquisition of a new artifact.

### Not established

- No result here proves silent installation of an arbitrary marketplace artifact.
- Goose's page does not establish whether dynamic enablement downloads new bytes, whether the candidate was previously registered,
  or whether a candidate-specific approval appears.
- `R3` does not prove authorization-binding weakness, ambient capability inheritance, or first-execution effects.
- The pass cannot support product-default or industry-prevalence claims.

## 5. Consequence for Htrans and the paper

The delegated-activation part of Htrans no longer needs to be introduced as wholly imaginary: it can be described as a controlled
instantiation of the **documented Goose Extension-Manager policy pattern**. The third-party-acquisition part remains unproven.
Htrans must not be described as a reproduction of Goose unless a later version-pinned source/canary audit proves provenance,
download/activation semantics, approval behavior, and behavioral equivalence.

The headline remains conditional. To keep Thesis B as the main claim, the subsequent audit must still show that, in a real
delegated path, the authorization object fails to remain bound through activation/first execution. If that evidence does not
materialize, the predeclared downgrade remains:

- real delegated-selection direction exists;
- authorization-binding weakness is not established across two systems;
- Htrans becomes design-space consequence analysis rather than a real-world vulnerability prevalence result.
