# 49 — Related Work v2（按"绑定对象 × 复核时刻"重组）

> 日期：2026-08-12
> 依赖：idea/42 Amendment 7（竞品边界与主张收缩）；idea/47（route grades）；idea/34 §8（旧版 related work）
> 用途：替换 idea/34 §8。正文为英文（投稿语言），中文段落是给自己的施工说明。
> **口径**：本节所有"we are the first / none of these"类表述，都必须能落到 A7.2 的
> "绑定对象 / 复核时刻 / 隐含假设"三列上；不能落到那三列的，一律删掉。

---

## 施工说明（中文，不进论文）

### 为什么重组

旧版 §8 按"攻击阶段"排（post-load / selection / endorsement / ecosystem）。那个轴现在不够用了，
因为新的竞品（SkillFortify、AgentBound、tdcommons、ToolHive）全是**防御机制**，
按攻击阶段排会把它们塞进"其他"里，而它们恰恰是最接近 C3 的。

新轴是论文自己的轴：**每个工作绑定什么、在哪一刻复核、隐含假设是什么。**
delta 就是那张表里空掉的那一格。

### 引用核实状态

| 状态 | 条目 |
|---|---|
| **本会话已核实**（拿到可抓取页面 + 正文片段） | AttestMCP 2601.17549；SkillFortify 2603.00195；AgentBound 2510.21236（FSE 2026, Article FSE096）；tdcommons 10604；MDPI 2624-800X/6/3/84；MDPI 18/5/243；CVE-2025-54136；Obot supply-chain blog；ToolHive docs；Invariant Labs tool poisoning notification；Microsoft Learn rug-pull entry；Elastic Security Labs |
| **由 codex 核实**（idea/47、idea/45 记录） | Goose v1.45.0 文档与源码；Claude Code plugin relevance；Cline MCP overview；Codex skills；OpenAI Agents SDK MCP；CrewAI MCP；AutoGen Workbench；Gemini CLI extensions；Continue MCP；OpenHands MCP |
| **待核实**（沿用 idea/15、idea/34，camera-ready 前须逐条回原文） | Skill-Inject 2602.20156；Poise 2606.07943；MCPTox 2508.14925；SkillTrojan 2604.06811；BadSkill 2604.09378；Semantic SC 2605.11418；ToolHijacker 2504.19793；ToolTweak 2510.02554；SCR 2606.15242；HalluSquatting 2607.07433；SearchGEO 2606.16821；Skills That Don't Exist 2607.12340；Neutral Prompting 2605.29354；You Told Me To Do It 2603.11862；Do Not Mention 2602.06547；OpenSkillRisk 2607.20121；SHE 2608.09885；MCP-Zero 2506.01056；MSB 2510.15994；MCPSecBench 2508.13220；AgentDojo 2406.13352；InjecAgent 2403.02691；Greshake 2302.12173；Beyond the Protocol 2506.02040；MCP-Guard 2508.10991 |

**未核实的一律不得写进 camera-ready。** 现阶段可以占位，但要在 `.bib` 里标 `VERIFY`。

### 三条不可越线

1. 不写"首次发现授权绑定到名字而非内容"——rug pull 与 CVE-2025-54136 已占；
2. 不写"首次为 agent skill 提出内容哈希绑定"——SkillFortify / MCPShield 已占；
3. 不写"没人在 activation 处设控制点 / 没人做 runtime confinement"——AgentBound 已占。

---

## 8. Related Work

Prior work on agent extension security can be read along two axes that matter for this paper:
**what an authorization is bound to**, and **at which moment that binding is checked**.
Organizing the literature this way makes the remaining gap visible: existing mechanisms bind at a
moment chosen by a human, and assume the artifact already exists at that moment.

### 8.1 What a loaded extension can do

A large body of work measures the consequences of a skill that is *already loaded into the agent's
context*. Skill-Inject reports high attack success from instructions hidden in skill files, and
Poise reaches comparable rates with a single setup line plus a side script while the user's task
still passes its verifier. MCPTox poisons real MCP tool descriptions, and skill-backdoor work
(SkillTrojan, BadSkill) pushes post-load success rates higher still. Runtime Skill Audit takes the
complementary view, probing what a skill-mediated agent actually does under targeted conditions
rather than testing every skill with generic tasks.

These works establish the *severity* of the final stage. They presuppose that the extension is
present and running: the question of which bytes became that extension, and under what
authorization, is outside their scope.

### 8.2 Retrieval and selection within a fixed registry

Closest on the pre-load side, work on SKILL.md semantics shows that a short trigger manipulates
registry discovery and that a one-sentence description change wins selection a majority of the time
across models. ToolHijacker frames tool use as retrieval plus selection and drives
document-optimized hijacking to high success on tools *already in the library*; ToolTweak lifts
selection among interchangeable tools substantially. MCP-Zero inverts the direction, letting a model
declare a capability gap and request tools on demand across a large server corpus — but what it
acquires is a *tool schema* from a configured universe, not third-party code to execute.

All of these operate over a candidate set whose membership was fixed beforehand.

### 8.3 Endorsement, install commands, and hallucinated names

Several works touch installation, each from a stronger starting point or stopping earlier on the
chain. SCR shows benign-in-isolation skills become harmful in composition; its neutral CapFlow
setting already uses non-imperative task language, and its TrustLift setting raises harmful
installation sharply — but from a *downstream install request* in a *simulated* market.
HalluSquatting measures real end-to-end install and code execution when the *user explicitly asks
to clone or install* a skill whose hallucinated name the attacker pre-registered. SearchGEO induces
an agent to endorse a skill and emit an install *command* but stops at command output; Skills That
Don't Exist measures recommendation hallucination with an explicit-authorization install
proof-of-concept; Neutral Prompting elicits a hallucinated package and an install string without
executing it; and You Told Me To Do It shows high compliance with adversarial README instructions.

Each reports a different endpoint from a different start. None follows a single trajectory from an
ordinary capability task through activation to first execution.

### 8.4 Protocol-level analyses of MCP

AttestMCP presents a security analysis of the MCP specification, identifying absent capability
attestation, unauthenticated sampling, and implicit trust propagation, and proposes a
backward-compatible extension adding capability attestation and message authentication, evaluated
over 847 attack scenarios. Related analyses (Beyond the Protocol; MCP-Guard; MCP threat-modeling
studies) map attack surfaces across the ecosystem and evaluate client-side validation.

These analyses target the *prompt-injection* layer: what a server may claim, what it may inject, and
whether a client can attribute a message's origin. The question of *which code the server process is
running* is orthogonal, and the attestation binds a server's declared capabilities and message
authenticity rather than the bytes that were resolved and executed.

### 8.5 Mutable tool definitions after approval: rug pulls and tool poisoning

A well-established practitioner line studies what happens when a server *changes* after the user has
approved it. Tool poisoning hides adversarial instructions in tool descriptions so that the model is
steered without the user seeing the payload. The "rug pull" pattern generalizes this to any
post-approval change: because the specification defines no mechanism to lock or version a tool
definition, a server can alter its tools after the trust relationship is established, and most hosts
do not re-prompt. CVE-2025-54136 (MCPoison) demonstrates the pattern concretely, showing a host that
continued to trust an approved configuration key after the underlying command had been swapped. The
pattern now appears in vendor attack catalogues and industry security guidance.

**We must distinguish our question from both.** Tool poisoning is an attack on the *prompt* layer:
the model is deceived by text it reads. Our subject is the *code identity* layer: the bytes that
execute are not the bytes that were authorized, whether or not any text is deceptive. And rug pulls
concern *attacker-controlled updates* — a malicious publisher pushing a change after approval. We
study authorization *binding*, and the gap we describe is present under entirely benign publisher
updates, ordinary dependency resolution, or registry compromise, because it follows from what the
authorization was attached to rather than from anyone's intent to attack.

Concretely: we do not require the publisher to be malicious, and we do not require any tool
description to change. In our construction the advertised tool surface is byte-identical across the
substitution.

### 8.6 Integrity and access-control mechanisms for agent extensions

The defensive literature has converged on binding *something* about an extension and re-checking it
later. SkillFortify provides a formal static-analysis framework for agent skills together with a
lockfile recording a content hash, declared capabilities, and resolution results; its guarantees are
static, and runtime enforcement is stated as future work. MCPShield takes a lockfile approach with
content hashes for tamper detection of server configurations. AgentBound introduces an access-control
framework for MCP servers with Android-style declarative permission manifests and a policy
enforcement engine, evaluated over the 296 most popular MCP servers, that requests user consent and
launches the server in a sandboxed environment with negligible overhead. A defensive publication by
Rosado pins a content hash over a server's complete advertised tool surface at import time, bound to
a per-server workload identity and the approving operator's identity, and re-checks it at every
subsequent advertisement and invocation. Deployment tooling such as ToolHive builds pinned container
images for protocol-scheme servers. In the broader supply chain, TUF, Sigstore, and in-toto establish
publisher authenticity, artifact integrity, and whole-chain verification.

These mechanisms are complementary to ours and we adopt rather than replace them: our permit takes a
digest and provenance as *input*. Two shared assumptions, however, bound their reach.

**First, the artifact must exist when the authorization is made.** A lockfile records what is on
disk; a surface pin hashes what a running server advertises; a signature attests bytes that were
built. An extension configured as `npx -y pkg@latest` or `uvx pkg` has no bytes at configuration
time — the command is a *recipe for obtaining bytes later*. Practitioner guidance states the
consequence plainly: every start downloads and executes whatever the registry serves at that moment,
with no pinning and no record of what ran.

**Second, a human decides when the server runs.** AgentBound's consent step and the surface pin's
approval moment both sit at a point where a person is configuring or importing a server.

### 8.7 Ecosystem measurement

Complementary measurement work establishes that malicious extensions exist and spread: large-scale
studies of skill marketplaces, MCP security benchmarks, and evaluations of risky skills across CLI
harnesses. These characterize the population of artifacts. In such evaluations the target skill is
typically already installed before a trial begins and the user prompt usually asks for it, so the
acquisition transition itself is not observed. Indirect prompt injection work establishes that
untrusted content can hijack agent actions, the mechanism behind our task-to-activation framing.

Safety-harness work is the closest on the *host* side: recent work attributes safety responsibility
to harness artifacts and learns boundaries from failure traces, including a case where an agent
expands a recommendation request into performing an application acquisition. That work governs
whether the agent should acquire at all; ours asks what the resulting authorization is attached to.

### 8.8 Positioning

Table N places each line by what it binds and when it checks.

| Work | Binds | Checked at | Assumes |
|---|---|---|---|
| Post-load attacks | — | — | extension already running |
| Selection / retrieval | — | — | candidate set fixed beforehand |
| SkillFortify | file content hash, declared capabilities | before installation (static) | artifact already on disk |
| MCPShield | config content hash | tamper check | artifact already on disk |
| AgentBound | permissions (fs, network) | consent, then sandboxed launch | a human decides when to launch |
| Surface pinning (Rosado) | advertised tool surface hash + workload identity | import, every advertise and invoke | a malicious change alters the surface |
| AttestMCP | declared capabilities, message authenticity | connection | threat is at the prompt layer |
| ToolHive | pinned container image | build | someone prebuilds the image |
| TUF / Sigstore / in-toto | publisher and artifact integrity | verification of built artifacts | artifact exists and is named |
| **This work** | **the resolved bytes, plus the use scope they were authorized for** | **resolution, activation, and first execution** | — |

Our delta is not content binding, which is well established, nor the observation that trust is bound
to a name rather than to content, which is documented and has an assigned CVE. It is that
**deferred-resolution selectors leave nothing for these mechanisms to bind at authorization time, and
agent-initiated activation moves the instant at which code is selected and executed past every
control point they occupy.** We measure where production systems place that instant, test whether it
precedes the first extension-tool authorization, and close the gap by inverting the order: resolve
into quarantine, compute the digest, authorize *those bytes* and a use scope, then materialize and
re-verify before first execution.

We do not claim to solve extension vetting, and we do not provide general runtime confinement; both
remain necessary and are addressed by the work above.

---

## 待办（中文）

1. `.bib` 建立，未核实条目标 `VERIFY`；camera-ready 前逐条回原文核对 ID、venue、年份。
2. §8.5 的切割段和 §8.6 的两条 assumption 是本节承重句，**不要在删减篇幅时先砍它们**。
3. Table N 的最后一行在 canary 出结果前保持现状；若 canary 未复现，按 idea/42 §9 降级，
   该行改为 design-space 表述。
4. §8.7 提到的 SHE、OpenSkillRisk 等条目待核实后补精确数字。
5. AgentBound 是唯一同行评审顶会竞品（FSE 2026），§8.6 与 §8.8 各出现一次，**不得弱化处理**。
