# Agent / Skill / MCP 安全文献速览

> 目的：先把这个领域的综述、benchmark 和最新论文读懂，再决定 slides 里应该借鉴哪些图、改哪些表述。  
> 当前项目主题可以定位为：**第三方 Skill / MCP Tool 作为 Agent 供应链入口时的信任边界问题**。

## 0. 建议阅读顺序

如果时间有限，按这个顺序读：

1. **Skill-Inject**：最贴近 `SKILL.md` 攻击，直接支撑本项目选题。
2. **MCPTox**：支撑“工具描述/metadata 投毒”，对应 T3。
3. **MSB / MCPSecBench**：支撑 MCP 真实生态与系统化 taxonomy。
4. **AgentDojo / InjecAgent**：支撑工具返回、网页、邮件等外部内容导致的间接提示注入，对应 T1/T4。
5. **LLM Agent Security Survey / LASM**：用来写背景、综述和未来工作。

汇报时不需要把所有论文都讲一遍。建议只讲 3 类：

- **综述**：说明这个方向已经是系统性研究问题。
- **MCP / Skill benchmark**：说明你的 `SKILL.md` 攻击不是凭空想象。
- **Agent prompt injection benchmark**：说明工具返回/外部内容注入是已知核心风险。

## 1. 综述类：建立研究框架

### 1.1 A Systematic Survey of Security Threats and Defenses in LLM-Based AI Agents: A Layered Attack Surface Framework

- 时间：2026
- 类型：综述 / taxonomy
- 链接：https://arxiv.org/abs/2604.23338
- 核心贡献：
  - 提出 **Layered Attack Surface Model (LASM)**。
  - 把 Agent 安全面拆成 7 层：Foundation、Cognitive、Memory、Tool Execution、Multi-Agent Coordination、Ecosystem、Governance。
  - 还加了时间维度：即时攻击、会话持久、跨会话累积、子会话栈传播。
  - 分析 2021-2026 年 116 篇论文。
- 和本项目的关系：
  - 我们主要落在 **Tool Execution** 和 **Ecosystem** 两层。
  - `SKILL.md` / MCP 属于生态与供应链入口。
  - `handler.py`、`TerminalTool` 属于工具执行层。
- 可借鉴图：
  - “Agent 安全分层图”：把我们的 T1-T4 标到 LASM 的 Tool Execution / Ecosystem 层上。
  - “攻击面 × 时间维度”矩阵：说明 T3 这类工具投毒可能是 session-persistent 控制点。

### 1.2 Security of LLM-based agents regarding attacks, defenses, and applications: A comprehensive survey

- 时间：2026
- 类型：综述
- 链接：https://doi.org/10.1016/j.inffus.2025.103941
- 核心贡献：
  - 系统整理 LLM agent 的攻击、防御和安全应用。
  - 强调 LLM agent 是带感知和行动模块的自治/半自治系统。
  - 讨论攻击和防御的评价标准。
- 和本项目的关系：
  - 可支撑“Agent 不只是聊天模型，因为它有 action/tool layer”。
  - 可作为 slides 背景页参考。
- 可借鉴图：
  - Agent 参考架构图：Input/Perception、Planning、Model Inference、Memory/Retrieval、Tool/Action。

### 1.3 Securing LLM-based agents against cyberattacks: a comprehensive survey on attack techniques and defense strategies

- 时间：2026
- 类型：综述，开放获取
- 链接：https://link.springer.com/article/10.1007/s11416-026-00622-3
- 核心贡献：
  - 采用五层参考架构：input/perception、orchestration/planning、model inference、memory/retrieval、tool/action。
  - 攻击分类包括 prompt/context manipulation、privacy attacks、agentic action induction 等。
  - 防御分类包括 sanitization、architectural safeguards、monitoring/guardrails、provenance。
- 和本项目的关系：
  - T1 属于 context manipulation。
  - T2 属于 privacy / secret leakage。
  - T4 属于 agentic action induction。
  - `skill_guard` 属于 sanitization + runtime guardrail 的教学级版本。
- 可借鉴图：
  - 五层 Agent 架构 + 每层攻击点。

## 2. Skill / MCP 相关：最贴近当前选题

### 2.1 Skill-Inject: Measuring Agent Vulnerability to Skill File Attacks

- 时间：2026
- 类型：benchmark
- 链接：
  - 论文：https://arxiv.org/abs/2602.20156
  - 项目页：https://www.skill-inject.com/
  - 代码：https://github.com/aisa-group/skill-inject
- 核心贡献：
  - 研究恶意指令隐藏在 agent skill files 中的攻击。
  - Benchmark 包含 202 个 injection-task pairs。
  - 攻击从明显恶意到上下文相关、伪装正常的 skill 指令。
  - 结果显示当前 agents 最高可到 80% ASR，并可能执行数据外泄、破坏性操作、类似 ransomware 的行为。
  - 论文认为这个问题不能靠模型规模或简单输入过滤解决，需要 context-aware authorization frameworks。
- 和本项目的关系：
  - 这是最直接支撑 `SKILL.md` 攻击面的论文。
  - 我们的 T1/T4 和它的 skill-file injection 很接近。
  - 我们的 `skill_guard` 也能对照它的结论：简单正则不是最终答案。
- 可借鉴图：
  - “Anatomy of Skill Injections”：正常 skill 文件中混入恶意步骤。
  - “模型 ASR 对比柱状图”：可以模仿成我们自己的 T1-T4 概念矩阵。
- 汇报可用一句话：
  - “Skill-Inject 说明，skill 文件本身已经被最新研究视为 agent 供应链攻击面；我们的实验是在 hello-agents 框架里复现这一类风险。”

### 2.2 MCPTox: A Benchmark for Tool Poisoning Attack on Real-World MCP Servers

- 时间：2025 / AAAI-26
- 类型：benchmark
- 链接：https://arxiv.org/abs/2508.14925
- 核心贡献：
  - 研究 **Tool Poisoning**：恶意指令嵌入 tool metadata / description，不需要执行恶意代码。
  - 基于 45 个真实 MCP servers、353 个真实 tools。
  - 构造约 1.3k 个恶意测试用例，覆盖 10 类风险。
  - 评测 20 个 LLM agents，部分模型 ASR 很高；论文指出更强的 instruction-following 可能反而更容易被 tool poisoning 利用。
  - safety alignment 对“合法工具执行未授权操作”效果有限。
- 和本项目的关系：
  - 对应 T3：`security_gate` 在 description 中写“必须先调用我”。
  - 支撑我们的论点：不需要恶意 handler，只要 metadata 被信任就能攻击。
- 可借鉴图：
  - “Tool metadata poisoning pipeline”：MCP server → tool description → LLM tool selection → unauthorized tool call。
  - “真实 MCP server / tools benchmark overview”。
- 汇报可用一句话：
  - “MCPTox 说明工具描述本身就是可投毒载体；这和我们 T3 的恶意 description 完全对应。”

### 2.3 MCP Security Bench (MSB): Benchmarking Attacks Against Model Context Protocol in LLM Agents

- 时间：2025
- 类型：benchmark / taxonomy
- 链接：https://arxiv.org/abs/2510.15994
- 核心贡献：
  - MCP 让 tools 成为 first-class、composable objects，并带有 natural-language metadata 与标准化 I/O。
  - MSB 覆盖完整 tool-use pipeline：task planning、tool invocation、response handling。
  - taxonomy 包含 12 类攻击：name-collision、preference manipulation、tool description prompt injection、out-of-scope parameter requests、user-impersonating responses、false-error escalation、tool-transfer、retrieval injection、mixed attacks 等。
  - 评测 9 个 LLM agents、10 个领域、400+ tools、2000 个攻击实例。
- 和本项目的关系：
  - T3 可以对应 tool description prompt injection / preference manipulation。
  - T4 可以对应 response handling 阶段的危险工具链。
  - 它的三阶段 pipeline 很适合替换我们现在偏泛化的流程图。
- 可借鉴图：
  - 三阶段 pipeline：Planning → Invocation → Response Handling。
  - 攻击类型 taxonomy 表。

### 2.4 MCPSecBench: A Systematic Security Benchmark and Playground for Testing Model Context Protocols

- 时间：2025
- 类型：benchmark / playground / taxonomy
- 链接：https://arxiv.org/abs/2508.13220
- 核心贡献：
  - 提出 MCP 安全 taxonomy：17 类攻击，4 个主要攻击面。
  - 集成 prompt datasets、MCP servers、MCP clients、attack scripts。
  - 评测多个 MCP provider；超过 85% 的攻击至少能攻破一个平台。
  - 核心漏洞在 Claude、OpenAI、Cursor 等平台上都有体现。
- 和本项目的关系：
  - 支撑“真实生态中 MCP/Skill 的攻击面不是单点 bug，而是系统层风险”。
  - 可帮助我们把 `SKILL.md` 四入口扩展成 MCP 四攻击面。
- 可借鉴图：
  - “4 primary attack surfaces” 图。
  - “MCP client/server/transport/tool layers” 图。

## 3. 间接提示注入与工具返回攻击

### 3.1 AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents

- 时间：2024
- 类型：benchmark
- 链接：https://arxiv.org/abs/2406.13352
- 核心贡献：
  - 评估 agents 在执行工具并处理不可信数据时的 prompt injection 风险。
  - 包含 97 个现实任务、629 个 security test cases。
  - 场景包括 email、e-banking、travel booking。
  - 论文强调：工具返回的不可信数据可能劫持 agent 去执行恶意任务。
- 和本项目的关系：
  - 直接对应 T1：工具返回值中夹带指令。
  - 也对应 T4：工具返回诱导 agent 调用另一个危险工具。
- 可借鉴图：
  - “trusted user instruction vs untrusted tool output” 边界图。
  - “agent reads external content → malicious instruction → unsafe tool call” 流程图。

### 3.2 InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated LLM Agents

- 时间：2024 / ACL Findings
- 类型：benchmark
- 链接：
  - ACL：https://aclanthology.org/2024.findings-acl.624/
  - arXiv：https://arxiv.org/abs/2403.02691
- 核心贡献：
  - 关注 tool-integrated LLM agents 的 indirect prompt injection。
  - 包含 1054 个 test cases、17 个 user tools、62 个 attacker tools。
  - 攻击意图分为两大类：direct harm to users 和 private data exfiltration。
  - 评测 30 个 LLM agents。
- 和本项目的关系：
  - T1 是 private data exfiltration。
  - T4 是 direct harm / destructive action。
- 可借鉴图：
  - “user tools vs attacker tools”的双工具系统图。
  - “external content embeds malicious instructions”的攻击示意。

### 3.3 BIPIA: Benchmarking and Defending Against Indirect Prompt Injection Attacks on LLMs

- 时间：2023/2024
- 类型：benchmark + defense
- 链接：https://arxiv.org/abs/2312.14197
- 核心贡献：
  - 早期系统研究 indirect prompt injection。
  - 提出 BIPIA benchmark。
  - 认为成功原因之一是 LLM 难以区分 information context 和 actionable instruction。
  - 提出 boundary awareness 和 explicit reminder 等防御。
- 和本项目的关系：
  - 可以支撑我们“工具返回要标记为不可信数据”的防御观点。
  - `skill_guard` 的返回消毒是 very small version；更系统的做法是边界感知和权限控制。
- 可借鉴图：
  - “上下文边界 / instruction-data separation”。

## 4. 工具执行与危险行为评估

### 4.1 ToolEmu: Identifying the Risks of LM Agents with an LM-Emulated Sandbox

- 时间：2023
- 类型：risk evaluation framework
- 链接：https://arxiv.org/abs/2309.15817
- 核心贡献：
  - 用 LM 模拟工具执行环境，评估 agent 使用高风险工具时的失败模式。
  - Benchmark 包含 36 个高风险工具、144 个测试用例。
  - 人工评估显示其发现的一部分 failures 可以对应真实世界风险。
- 和本项目的关系：
  - 对应 T4：Agent 使用 terminal 或外部工具时，错误/恶意调用会造成真实副作用。
  - 支撑“危险工具不应完全交给模型决定”。
- 可借鉴图：
  - “Agent → Tool Emulator → Risk Evaluator”的评测架构。

## 5. 防御与 guardrail 方向

### 5.1 ClawGuard: A Runtime Security Framework for Tool-Augmented LLM Agents Against Indirect Prompt Injection

- 时间：2026
- 类型：defense framework
- 链接：https://arxiv.org/abs/2604.11790
- 和本项目的关系：
  - 适合对照 `skill_guard`。
  - 强调 runtime boundary enforcement，而不是只靠 prompt。
- 可借鉴图：
  - “policy gate / monitor 位于 LLM 和 tool-call boundary 之间”的图。

### 5.2 AgentSentry: Mitigating Indirect Prompt Injection in LLM Agents via Temporal Causal Diagnostics and Context Purification

- 时间：2026
- 类型：defense
- 链接：https://arxiv.org/abs/2602.22724
- 核心贡献：
  - 把 multi-turn IPI 看成 temporal causal takeover。
  - 在 AgentDojo 上评估。
- 和本项目的关系：
  - 支撑“攻击不一定是一轮完成，可以跨多轮逐步接管上下文”。
  - 可用于未来工作页。

## 6. 本项目如何定位

当前项目可以写成：

> 我们复现并教学化展示了第三方 `SKILL.md + handler.py` 在 Agent 系统中的四类信任边界破坏：工具返回注入、handler 权限滥用、工具描述投毒、工具链越权执行。该实验可视为 Skill-Inject / MCPTox / AgentDojo 等最新研究在 hello-agents 框架中的一个小型、受控、可讲解复现。

不要说：

- “我们发现了全新的漏洞。”
- “我们证明所有 Agent 都不安全。”
- “我们的正则防御完全解决问题。”

建议说：

- “我们围绕最新文献中的 Skill / MCP / tool-use attack surface，做了一个受控复现实验。”
- “重点不是攻击真实系统，而是解释为什么第三方 skill 应被视为不可信供应链组件。”
- “`skill_guard` 是教学级防御原型，用来说明防御应放在 description、handler、tool result、terminal boundary 上。”

## 7. 下一轮 slides 可以重画的核心图

### 图 1：Agent 安全分层图

参考：

- LASM survey
- Springer survey 的五层 Agent 架构

画法：

```text
User/Input
  ↓
Agent Planner / LLM
  ↓
Tool Registry / Skill Metadata
  ↓
Handler Runtime
  ↓
File / Env / Network / Terminal
```

把攻击标上去：

- T1：Tool Result → LLM
- T2：Handler Runtime → Env/Network
- T3：Skill Metadata → Tool Selection
- T4：Tool Result → Terminal → File

### 图 2：SKILL.md 文件剖面图

参考：

- Skill-Inject 的 “Anatomy of Skill Injections”

画法：

```text
skill/
  SKILL.md
    frontmatter.name
    frontmatter.description   ← T3
    body/instructions         ← T1
  handler.py                  ← T2/T4
  tool output                 ← T1/T4
```

### 图 3：MCP Tool Poisoning Pipeline

参考：

- MCPTox
- MSB

画法：

```text
Attacker MCP Server
  ↓ poisoned metadata
MCP Client / Tool Discovery
  ↓ tool descriptions enter context
LLM Planning / Tool Selection
  ↓ unauthorized tool call
Sensitive Action / Exfiltration
```

### 图 4：Defense Matrix

参考：

- MCPSecBench taxonomy
- ClawGuard / AgentSentry runtime defense

画法：

| 防御点 | T1 | T2 | T3 | T4 |
|---|---|---|---|---|
| Static scan | 部分 | 部分 | 部分 | 部分 |
| Tool result sanitization | 有效 | - | - | 部分 |
| Env isolation | - | 有效 | - | - |
| Command gate | - | - | - | 有效 |
| Sandbox | 需要 | 需要 | 部分 | 需要 |
| Human approval | 部分 | 部分 | 部分 | 需要 |

## 8. 参考文献列表

1. Kexin Chu. *A Systematic Survey of Security Threats and Defenses in LLM-Based AI Agents: A Layered Attack Surface Framework*. arXiv:2604.23338. https://arxiv.org/abs/2604.23338
2. David Schmotz, Luca Beurer-Kellner, Sahar Abdelnabi, Maksym Andriushchenko. *Skill-Inject: Measuring Agent Vulnerability to Skill File Attacks*. arXiv:2602.20156. https://arxiv.org/abs/2602.20156
3. Zhiqiang Wang et al. *MCPTox: A Benchmark for Tool Poisoning Attack on Real-World MCP Servers*. arXiv:2508.14925. https://arxiv.org/abs/2508.14925
4. Dongsen Zhang et al. *MCP Security Bench (MSB): Benchmarking Attacks Against Model Context Protocol in LLM Agents*. arXiv:2510.15994. https://arxiv.org/abs/2510.15994
5. Yixuan Yang, Daoyuan Wu, Yufan Chen. *MCPSecBench: A Systematic Security Benchmark and Playground for Testing Model Context Protocols*. arXiv:2508.13220. https://arxiv.org/abs/2508.13220
6. Edoardo Debenedetti et al. *AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents*. arXiv:2406.13352. https://arxiv.org/abs/2406.13352
7. Qiusi Zhan et al. *InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Large Language Model Agents*. ACL Findings 2024. https://aclanthology.org/2024.findings-acl.624/
8. Jingwei Yi et al. *Benchmarking and Defending Against Indirect Prompt Injection Attacks on Large Language Models*. arXiv:2312.14197. https://arxiv.org/abs/2312.14197
9. Yangjun Ruan et al. *Identifying the Risks of LM Agents with an LM-Emulated Sandbox*. arXiv:2309.15817. https://arxiv.org/abs/2309.15817
10. *Securing LLM-based agents against cyberattacks: a comprehensive survey on attack techniques and defense strategies*. Springer, 2026. https://link.springer.com/article/10.1007/s11416-026-00622-3
